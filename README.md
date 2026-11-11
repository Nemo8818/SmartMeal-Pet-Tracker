# SmartMeal – My Little Healthy Pet

SmartMeal is a single-user university programming project that combines a food
diary and everyday wellness trackers with a small virtual-pet game. Log meals,
water, and movement to earn capped XP and help a mystery egg grow through five
stages.

## Features

- Profile with age, gender, height, weight, activity level, and health goal
- Mifflin–St Jeor BMR and TDEE estimates, with moderate calorie adjustments
- A 1,500 kcal minimum for generic adult weight-loss targets; no generic target
  is shown for users under 18 or estimates outside the app's general-use range
- Thai food library with estimated calories, protein, carbohydrates, and fat,
  plus custom foods
- Add and delete meals, water entries, activities, and weight measurements
- Water and activity progress, plus a Matplotlib weight-history chart
- Cat, rabbit, dog, bear, or penguin mystery egg that hatches after 30 XP
- XP for logging meals, water, movement, and one daily care check-in, with daily
  caps; no XP for eating less, weight loss, or weight changes
- SQLite local storage, Pandas summaries, and optional fictional sample data
- Responsive pastel styling for the Streamlit interface

## Run locally

You need Python 3.10 or newer.

1. Download or clone this project folder.
2. Open a terminal in the folder containing `app.py`.
3. Create and activate a virtual environment:

   **macOS / Linux**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   **Windows PowerShell**

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

4. Install the libraries:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Start the app:

   ```bash
   streamlit run app.py
   ```

6. Open the local URL Streamlit prints in the terminal. Create a profile, or
   choose **Load sample demo data** for a class presentation.

The first run creates `smartmeal.db` beside `app.py`. That file contains your
profile and logs. Keep a backup if you want to preserve your data, and do not
upload it to a public repository.

## Run in Replit

The project can also be run in Replit with the dependencies in
`requirements.txt`. Start the SmartMeal workflow/preview, or run:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 5000
```

The application uses a local SQLite file and is intended for one user at a
time. It does not provide cloud sync, user accounts, or multi-user data
separation.

## Upload the project to a public GitHub repository

Do not include your database or personal health records in a public repository.
The supplied `.gitignore` excludes the SQLite database and local Python files.

### GitHub website

1. Sign in to GitHub and choose **New repository**.
2. Enter a repository name such as `smartmeal-healthy-pet` and select **Public**.
3. Create the repository without adding a README, license, or `.gitignore`
   (these files are already in this project).
4. In the new repository, choose **Add file → Upload files**.
5. Upload `app.py`, `smartmeal_data.py`, `requirements.txt`, `README.md`, and
   `.gitignore`.
6. Review the file list to make sure `smartmeal.db` is not included, add a
   commit message, and choose **Commit changes**.

### Git command line

For a standalone repository, first put the five project files above in a clean
folder, then run:

```bash
git init -b main
git add app.py smartmeal_data.py requirements.txt README.md .gitignore
git commit -m "Add SmartMeal healthy pet app"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Replace the GitHub URL with the URL for your new repository. If Git asks you
to authenticate, use GitHub's supported sign-in flow; do not put a password or
token in this project.

## Important health note

SmartMeal is an educational demo, not a medical or dietetic service. Food
values, activity calories, BMR, and TDEE are estimates. Calorie estimates are
for adults only, use modest adjustments, and are suppressed when the calculated
maintenance estimate is outside a broad general-use range. Ask a qualified
health professional for personal advice, especially for minors, pregnancy,
medical conditions, or special dietary needs.
