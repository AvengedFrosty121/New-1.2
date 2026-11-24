# Plumber's Job Kit

A phone web app for plumbers. Open it in your phone's browser and add it to your home screen; it then works like an app, including offline.

- **Jobs** — track customers, addresses and work, and move each job from Scheduled → In progress → Done.
- **Quote** — tap parts to add them, set labor hours, rate, markup, tax and trip fee, then copy the quote as text to text or email a customer.
- **Calcs** — water volume in a pipe run, drain slope fall, pressure at a raised fixture, and water heater sizing.

Data is saved on the phone itself (browser storage). The parts prices are examples; edit them to yours.

## Put it on your phone
It needs to be served over HTTPS. The easiest free option is GitHub Pages: in the repo's **Settings → Pages**, pick this branch and the root folder, then open `https://<your-username>.github.io/<repo>/plumbing-app/` on your phone and choose **Add to Home Screen** (Safari share menu on iPhone, ⋮ menu on Android).

## Editing
Edit `app.html`, then run `./build.sh` to regenerate `index.html`.
