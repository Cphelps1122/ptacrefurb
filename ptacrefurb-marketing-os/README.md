# PTAC Refurb Marketing OS

A lightweight marketing operating system for PTAC Refurb: lead tracking, content performance, website roadmap, executive KPIs, and a Streamlit dashboard.

## What is included

```text
ptacrefurb-marketing-os/
├── dashboard/
│   └── app.py
├── data/
│   └── PTAC_Refurb_Marketing_OS.xlsx
├── automation/
│   └── google_apps_script_marketing_os.gs
├── docs/
│   ├── PTAC_Refurb_Marketing_Director_Playbook.docx
│   └── PTAC_Lead_Intake_Form_Questions.md
├── .streamlit/
│   └── secrets.toml.example
├── requirements.txt
├── .gitignore
└── README.md
```

## Fast local test

1. Open Terminal or VS Code in this folder.
2. Install packages:

```bash
pip install -r requirements.txt
```

3. Run the dashboard:

```bash
streamlit run dashboard/app.py
```

The dashboard uses the spreadsheet in `data/PTAC_Refurb_Marketing_OS.xlsx` by default.

## GitHub setup

1. Create a new GitHub repo named `ptacrefurb-marketing-os`.
2. Add this folder to the repo.
3. Commit and push:

```bash
git init
git add .
git commit -m "Initial PTAC Refurb Marketing OS"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/ptacrefurb-marketing-os.git
git push -u origin main
```

## Streamlit Cloud deployment

1. Go to Streamlit Community Cloud.
2. Connect your GitHub repo.
3. Main file path: `dashboard/app.py`.
4. Deploy.

## Recommended first workflow

For the first week, keep it simple:

1. Update the Excel workbook every Friday.
2. Push the updated workbook to GitHub.
3. Streamlit will refresh after redeploy/restart.

Once the process is stable, move the workbook to Google Sheets and connect the dashboard using CSV links in Streamlit secrets.

## Optional Google Sheets connection

1. Upload `PTAC_Refurb_Marketing_OS.xlsx` to Google Drive.
2. Open it with Google Sheets.
3. For each tab, publish the tab as CSV.
4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` locally or add the same values in Streamlit Cloud secrets.
5. Paste the CSV links under `[google_sheets]`.
6. In the dashboard sidebar, choose `Use Google Sheet CSV links`.

## Apps Script automation

1. Open the Google Sheet.
2. Go to Extensions > Apps Script.
3. Paste the code from `automation/google_apps_script_marketing_os.gs`.
4. Change `EMAIL_TO` to your email address.
5. Save.
6. Reload the Google Sheet and use the `PTAC Marketing OS` menu.

## Day 1 baseline checklist

Before posting or editing anything, document:

- LinkedIn followers
- LinkedIn impressions/profile views if available
- Facebook followers/reach if available
- Website monthly visitors if available
- Current quote requests
- Current open opportunities
- Current closed sales attributed to marketing, if any

Save screenshots in a folder named `Baseline`.
