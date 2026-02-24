import argparse
import csv
import datetime as dt
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup


BASE_URL = "https://casesearch.courts.state.md.us/casesearch"


@dataclass
class ChargeRecord:
    case_number: str
    defendant_name: str
    officer_name: str
    charge: str
    charge_description: str
    plea: str
    disposition: str
    case_status: str
    scraped_at: str


def _normalize_lines(text: str) -> List[str]:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return [line for line in lines if line]


def _find_section(lines: List[str], start_label: str, end_label: Optional[str]) -> List[str]:
    try:
        start_idx = lines.index(start_label)
    except ValueError:
        return []

    if end_label is None:
        return lines[start_idx + 1 :]

    try:
        end_idx = lines.index(end_label, start_idx + 1)
    except ValueError:
        end_idx = len(lines)

    return lines[start_idx + 1 : end_idx]


def _find_first_value_after_label(lines: List[str], label: str) -> str:
    for i, line in enumerate(lines):
        if line == label and i + 1 < len(lines):
            return lines[i + 1]
        if line.startswith(label):
            return line.replace(label, "", 1).strip()
    return ""


def _abs_url(action: str) -> str:
    if action.startswith("http"):
        return action
    if action.startswith("/"):
        return "https://casesearch.courts.state.md.us" + action
    return "https://casesearch.courts.state.md.us/casesearch/" + action.lstrip("./")


def _locate_case_form(html: str) -> Tuple[str, Dict[str, str], str, str]:
    soup = BeautifulSoup(html, "lxml")
    form = None
    for candidate in soup.find_all("form"):
        if candidate.find("input", {"type": "text"}):
            form = candidate
            break
    if not form:
        raise RuntimeError("Unable to locate case number form.")

    action = _abs_url(form.get("action") or BASE_URL)
    method = (form.get("method") or "get").lower()
    payload: Dict[str, str] = {}
    case_field_name = ""

    for inp in form.find_all("input"):
        name = inp.get("name")
        if not name:
            continue
        inp_type = (inp.get("type") or "").lower()
        value = inp.get("value", "")
        if inp_type == "text":
            case_field_name = name
        else:
            payload[name] = value

    if not case_field_name:
        raise RuntimeError("Unable to identify case number field.")
    return action, payload, case_field_name, method


def _parse_case_detail(case_number: str, html: str) -> List[ChargeRecord]:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)
    lines = _normalize_lines(text)

    lower_text = " ".join(lines).lower()
    if "data not found" in lower_text or any(
        "no cases" in line.lower() or "no case" in line.lower() for line in lines
    ):
        return [
            ChargeRecord(
                case_number=case_number,
                defendant_name="",
                officer_name="",
                charge="",
                charge_description="",
                plea="",
                disposition="",
                case_status="dismissed",
                scraped_at=dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            )
        ]

    defendant_section = _find_section(lines, "Defendant Information", "Involved Parties Information")
    defendant_name = _find_first_value_after_label(defendant_section, "Name:")

    parties_section = _find_section(lines, "Involved Parties Information", "Court Scheduling Information")
    officer_name = ""
    if parties_section:
        # Narrow to officer subsection if present
        if "Officer - Arresting/Complainant" in parties_section:
            officer_sub = _find_section(
                parties_section, "Officer - Arresting/Complainant", "Plaintiff"
            )
            officer_name = _find_first_value_after_label(officer_sub, "Name:")
        if not officer_name:
            officer_name = _find_first_value_after_label(parties_section, "Name:")

    charge_section_lines = _find_section(
        lines, "Charge and Disposition Information", "Document Information"
    )
    charge_text = "\n".join(charge_section_lines)

    plea_match = re.search(r"Plea:\s*(.*?)(?:Plea Date:|Disposition:|Disposition Date:|$)", charge_text, re.S)
    plea = plea_match.group(1).strip() if plea_match else ""

    disposition_match = re.search(
        r"Disposition:\s*(.*?)(?:Disposition Date:|Sentence|$)", charge_text, re.S
    )
    disposition = disposition_match.group(1).strip() if disposition_match else ""

    charge_records: List[ChargeRecord] = []
    charge_pattern = re.compile(
        r"Charge No:\s*(\d+).*?Statute Code:\s*([^\n]+?)\s+Charge Description:\s*([^\n]+)",
        re.S,
    )
    for match in charge_pattern.finditer(charge_text):
        charge_no = match.group(2).strip()
        charge_desc = match.group(3).strip()
        charge_records.append(
            ChargeRecord(
                case_number=case_number,
                defendant_name=defendant_name,
                officer_name=officer_name,
                charge=charge_no,
                charge_description=charge_desc,
                plea=plea,
                disposition=disposition,
                case_status="found",
                scraped_at=dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            )
        )

    if not charge_records:
        charge_records.append(
            ChargeRecord(
                case_number=case_number,
                defendant_name=defendant_name,
                officer_name=officer_name,
                charge="",
                charge_description="",
                plea=plea,
                disposition=disposition,
                case_status="found",
                scraped_at=dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            )
        )

    return charge_records


def _fetch_case_html_playwright(
    case_numbers: List[str],
    debug_html_path: Optional[str],
    headed: bool,
    delay_seconds: float,
    user_data_dir: str,
) -> List[Tuple[str, str]]:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required. Install with: pip install playwright "
            "and then run: python -m playwright install"
        ) from exc

    results: List[Tuple[str, str]] = []
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=not headed,
        )
        page = context.new_page()

        for case_number in case_numbers:
            page.goto(BASE_URL, wait_until="domcontentloaded")

            # Handle disclaimer if present
            try:
                agree_button = page.get_by_role("button", name=re.compile(r"agree", re.I))
                if agree_button.count() > 0:
                    agree_button.first.click()
                    page.wait_for_load_state("domcontentloaded")
                else:
                    agree_input = page.locator("input[value*='Agree' i], input[value*='I Agree' i]")
                    if agree_input.count() > 0:
                        agree_input.first.click()
                        page.wait_for_load_state("domcontentloaded")
            except PlaywrightTimeoutError:
                pass

            # If bot protection is shown, let user solve it in headed mode.
            if headed and (
                page.locator("iframe[title*='captcha' i]").count() > 0
                or "captcha-delivery.com" in page.content()
            ):
                print("CAPTCHA detected. Please solve it in the opened browser.")
                input("Press Enter here once the CAPTCHA is solved...")
                page.wait_for_load_state("domcontentloaded")

            if debug_html_path:
                with open(debug_html_path, "w", encoding="utf-8") as f:
                    f.write(page.content())

            case_input = _locate_case_input(page)
            case_input.fill(case_number)

            search_button = page.get_by_role("button", name=re.compile(r"search", re.I))
            if search_button.count() > 0:
                search_button.first.click()
            else:
                search_input = page.locator("input[value='Search'], input[value*='Search' i]")
                if search_input.count() > 0:
                    search_input.first.click()
                else:
                    case_input.press("Enter")

            page.wait_for_load_state("domcontentloaded")
            html = page.content()
            results.append((case_number, html))
            if delay_seconds > 0:
                time.sleep(delay_seconds)

        context.close()

    return results


def _locate_case_input(page):
    # Try common selectors on main page
    selectors = [
        "input#caseNumber",
        "input[name='caseId']",
        "input[aria-label*='Case Number' i]",
        "input[placeholder*='Case Number' i]",
        "input[name*='case' i]",
        "input[id*='case' i]",
        "input[type='text']",
    ]
    for sel in selectors:
        locator = page.locator(sel).first
        try:
            locator.wait_for(state="visible", timeout=8000)
            return locator
        except Exception:
            pass

    # Fallback: search within iframes
    for frame in page.frames:
        if frame == page.main_frame:
            continue
        for sel in selectors:
            locator = frame.locator(sel).first
            try:
                locator.wait_for(state="visible", timeout=8000)
                return locator
            except Exception:
                pass

    raise RuntimeError("Unable to locate case number input field.")


def scrape_case_numbers(
    case_numbers: List[str],
    debug_html_path: Optional[str],
    headed: bool,
    delay_seconds: float,
    user_data_dir: str,
) -> List[ChargeRecord]:
    all_records: List[ChargeRecord] = []
    for case_number, html in _fetch_case_html_playwright(
        case_numbers, debug_html_path, headed, delay_seconds, user_data_dir
    ):
        records = _parse_case_detail(case_number, html)
        all_records.extend(records)
    return all_records


def _load_case_numbers(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "case_number" not in reader.fieldnames:
            raise ValueError("Input CSV must include a 'case_number' header.")
        return [
            (row.get("case_number") or "").strip()
            for row in reader
            if (row.get("case_number") or "").strip()
        ]


def _write_csv(path: str, records: List[ChargeRecord]) -> None:
    fieldnames = [
        "case_number",
        "defendant_name",
        "officer_name",
        "charge",
        "charge_description",
        "plea",
        "disposition",
        "case_status",
        "scraped_at",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape MD case search by case number.")
    parser.add_argument(
        "--input",
        default="case_status/inputs.csv",
        help="CSV file with a case_number header.",
    )
    parser.add_argument("--output", default="case_status/case_results.csv", help="Output CSV path.")
    parser.add_argument(
        "--debug-html",
        default=None,
        help="Optional path to dump the loaded HTML before searching for the case input.",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run with a visible browser window (useful for solving CAPTCHAs).",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=2.0,
        help="Delay between case searches to reduce bot detection.",
    )
    parser.add_argument(
        "--user-data-dir",
        default="case_status/.playwright_user_data",
        help="Persistent Playwright profile directory for cookies/session.",
    )
    args = parser.parse_args()

    case_numbers = _load_case_numbers(args.input)
    records = scrape_case_numbers(
        case_numbers,
        args.debug_html,
        args.headed,
        args.delay_seconds,
        args.user_data_dir,
    )
    _write_csv(args.output, records)


if __name__ == "__main__":
    main()
