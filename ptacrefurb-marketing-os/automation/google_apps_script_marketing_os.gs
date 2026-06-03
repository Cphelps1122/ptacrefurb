/**
 * PTAC Refurb Marketing OS - Google Apps Script
 * Install inside your Google Sheet: Extensions > Apps Script.
 * Update EMAIL_TO before using.
 */
const EMAIL_TO = "your-email@example.com";
const LEADS_SHEET = "Leads CRM";
const REPORT_SHEET = "Monthly Report";
const HEADER_ROW = 4;

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("PTAC Marketing OS")
    .addItem("Send Follow-Up Reminders", "sendFollowUpReminders")
    .addItem("Email Monthly Summary", "emailMonthlySummary")
    .addItem("Create 9 AM Daily Follow-Up Trigger", "createDailyFollowUpTrigger")
    .addToUi();
}

function getSheet_(name) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(name);
  if (!sheet) throw new Error(`Missing sheet: ${name}`);
  return sheet;
}

function getRows_(sheetName) {
  const sheet = getSheet_(sheetName);
  const values = sheet.getDataRange().getValues();
  const headers = values[HEADER_ROW - 1].map(h => String(h).trim());
  const rows = values.slice(HEADER_ROW);
  const idx = Object.fromEntries(headers.map((h, i) => [h, i]));
  return { sheet, values, headers, rows, idx };
}

function sendFollowUpReminders() {
  const { rows, idx } = getRows_(LEADS_SHEET);
  const today = new Date();
  today.setHours(23, 59, 59, 999);
  let due = [];

  rows.forEach(row => {
    const company = row[idx["Company"]];
    if (!company) return;
    const contact = row[idx["Contact Name"]];
    const status = row[idx["Status"]];
    const next = row[idx["Next Follow-Up"]];
    if (next instanceof Date && next <= today && status !== "Won" && status !== "Lost") {
      due.push(`${company} | ${contact || "No contact"} | ${status || "No status"}`);
    }
  });

  if (due.length === 0) {
    SpreadsheetApp.getUi().alert("No follow-ups are due today.");
    return;
  }

  MailApp.sendEmail({
    to: EMAIL_TO,
    subject: `PTAC Refurb: ${due.length} follow-up(s) due`,
    body: "Follow up with these leads today:\n\n" + due.join("\n")
  });
  SpreadsheetApp.getUi().alert(`Sent ${due.length} follow-up reminder(s).`);
}

function emailMonthlySummary() {
  const report = getSheet_(REPORT_SHEET);
  const values = report.getRange("A4:B20").getDisplayValues();
  let body = "PTAC Refurb Monthly Marketing Summary\n\n";
  values.forEach(([label, value]) => {
    if (label || value) body += `${label}: ${value || "Not entered yet"}\n`;
  });
  MailApp.sendEmail({
    to: EMAIL_TO,
    subject: "PTAC Refurb Monthly Marketing Summary",
    body
  });
  SpreadsheetApp.getUi().alert("Monthly summary emailed.");
}

function createDailyFollowUpTrigger() {
  ScriptApp.newTrigger("sendFollowUpReminders")
    .timeBased()
    .everyDays(1)
    .atHour(9)
    .create();
  SpreadsheetApp.getUi().alert("Daily 9 AM follow-up trigger created.");
}

/**
 * Optional: connect a Google Form to this sheet, then set this function as an installable
 * trigger: Triggers > Add Trigger > onFormSubmit > From spreadsheet > On form submit.
 * The script appends form submissions to Leads CRM.
 */
function onFormSubmit(e) {
  const sheet = getSheet_(LEADS_SHEET);
  const named = e.namedValues || {};
  const get = (name) => (named[name] && named[name][0]) ? named[name][0] : "";

  sheet.appendRow([
    "",                         // Lead ID formula can be filled down in the sheet
    new Date(),                  // Date Added
    get("Company"),
    get("Contact Name"),
    get("Title/Role"),
    get("Email"),
    get("Phone"),
    get("Property Type"),
    get("City/State"),
    get("Source") || "Website Form",
    get("Estimated Units"),
    get("Estimated Unit Price") || 425,
    get("Estimated Opportunity Value"),
    "New",
    "",
    "",
    get("Notes")
  ]);

  MailApp.sendEmail({
    to: EMAIL_TO,
    subject: "New PTAC Refurb lead added",
    body: `New lead added:\n\nCompany: ${get("Company")}\nContact: ${get("Contact Name")}\nEmail: ${get("Email")}\nPhone: ${get("Phone")}\nUnits: ${get("Estimated Units")}\nNotes: ${get("Notes")}`
  });
}
