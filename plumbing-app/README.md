# 45° Offset Calculator

A simple phone app that gives the length of pipe to cut for a 45° offset.

1. Pick the **type of pipe**, **pipe size** and **fitting brand**.
2. Enter the **take-off** for that 45 once. It's saved on your phone for that pipe, size and brand, so next time you only pick from the dropdowns.
3. Enter the **offset**, center of pipe to center of pipe.

The result window draws the offset and labels the offset, run, travel and the cut piece.

**Math:** travel = offset × 1.414 · cut piece = travel − (take-off × 2), rounded to the nearest 1/16″.

**Take-off** is the distance from the center of the 45 (where its two centerlines cross) to where the pipe stops in it: the socket bottom or hub shoulder on glue and solder fittings, or the end of thread engagement on threaded fittings. Manufacturers' dimension sheets list it, usually as "G" or "center to socket bottom".

## Put it on your phone
It needs to be served over HTTPS; GitHub Pages is the easiest free option. In the repo's **Settings → Pages**, pick this branch and the root folder, then open `https://<your-username>.github.io/<repo>/plumbing-app/` on your phone and choose **Add to Home Screen**. It works offline after that.

## Editing
Edit `app.html`, then run `./build.sh` to regenerate `index.html`.
