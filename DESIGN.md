# Design for What's The Move Harvard: A Breakdown of Choices

Welcome to WTM Harvard! Our website is made by students for students to find all of the best parties and social events going on at Harvard and the greater Cambridge-Allston area. Designed with your ease in mind, WTM Harvard is easy to navigate and interact with. Additionally, it is meant to be another social platform for Harvard students, where we can all keep each other in the loop and outside of our studies now and then. Below is each design feature of WTM Harvard's website, as well as the thought process that went behind implementing each.

# Home


# Parties

## Interactive Party Map

The interactive map required four main pieces: storing coordinates in the database, converting location names to coordinates, creating an API to send party data, and using JavaScript to draw the map. I added `latitude` and `longitude` columns to the parties table.

For geocoding (converting "Lowell House" to GPS coordinates), I created a Python dictionary called `HARVARD_SQUARE_LOCATIONS` that maps location names to coordinate pairs. I manually looked up coordinates for all the houses, major buildings, and common spots on Google Maps. The `geocode_location()` function does case-insensitive partial matching, so "Lowell," "lowell house," and "LOWELL HOUSE" all match. If no match is found, it defaults to Harvard Square coordinates.

I made an API endpoint at `/api/parties/map` that returns party data in JSON format. The SQL query joins parties with users (to get verified host names), filters for upcoming parties with valid coordinates, and returns everything as JSON. This separates data retrieval from display, and the JavaScript just asks the API for data and the API handles all the database stuff.

For the actual map I used Leaflet.js with OpenStreetMap tiles. The JavaScript creates a map centered on Harvard Square, fetches party data from my API, and loops through each party to create markers. Each marker has a popup showing party details. The `fetch()` function is asynchronous, meaning it doesn't freeze the page while waiting for data.

I chose a custom location dictionary over Google Maps API because: (1) Google costs money after you hit usage limits, (2) I don't depend on external services, and (3) for Harvard-specific locations, my curated list is actually more accurate. The tradeoff is it only works for predefined locations, but Harvard parties mostly happen at known spots anyway. I separated the API from the display so the data could be reused elsewhere and each piece of code does one job cleanly. I only show upcoming parties to keep the map relevant and performant.

Host Verification Security System

The verification system akes sure that party creators are actually the hosts by requiring the host name to match the logged-in user's username. When someone submits the party form, my Flask route queries the database to get the current user's `display_name`, then compares it to the submitted `host_name` using case-insensitive matching (`.lower()` on both strings). If they don't match, I return an error page showing what their actual username is. This check happens on every party creation AND edit, preventing someone from creating a party correctly then editing it to change the host later.

I use parameterized SQL queries (`SELECT display_name FROM users WHERE id = ?`) instead of string concatenation to prevent SQL injection attacks. The `?` placeholder gets safely replaced with the actual value by the database library. I pre-fill the host name field with the user's username in the template to make the form easier and hint at the requirement. The error message explicitly shows their username so they know exactly what to type.

On the frontend, I display a green "✓ Verified Host" badge on all parties. Since parties can only be created by authenticated users whose host names match their usernames, every party is inherently verified. The badge builds trust and shows users the system is working.

I implemented this serverside instead of clientside because clientside JavaScript can be bypassed by anyone who opens browser dev tools. Serverside validation is authoritative - it controls what gets saved to the database. The tradeoff is less flexibility (you can't create parties on behalf of groups or other people), but I decided authenticity and trust were more important than convenience. Case insensitive matching (`kelly` = `Kelly`) is userfriendly without compromising any of the security since usernames aren't case sensitive anyway. Pre filling the host name field improves UX while the error message with the actual username prevents frustration from users who don't remember their exact username.



# Feed

## Photo Upload System (Posts and Party Flyers)

The photo upload system works the same way for both feed posts and party flyers, I just implemented it in two different routes. I added `photo_path TEXT` to the posts table and `flyer_path TEXT` to the parties table to store file paths (like "uploads/posts/20251207_183045_photo.jpg"). I store paths instead of the actual image data because file systems are better at serving files while databases are better at querying data. The paths are relative to the `static` directory which Flask automatically serves.

I configured upload settings in `app.py`, an upload folder location, allowed extensions (png, jpg, jpeg, gif only), and a 16MB max file size. The HTML forms need `enctype="multipart/form-data"` or file uploads won't work - this tells the browser to send file data in a special format. When a file is uploaded, I check if it exists, validate the extension with `allowed_file()`, sanitize the filename with `secure_filename()` to prevent malicious filenames like "../../hack.jpg", prepend a timestamp to make it unique, save it to the appropriate folder, and store the path in the database.

The timestamp prepending is crucial for preventing filename conflicts. If two users both upload "party.jpg," the second would overwrite the first without timestamps. By adding the date and time like "20251207_183045_party.jpg," every file is guaranteed to be unique. I chose 16MB as the max size because it's big enough for high-quality smartphone photos but small enough to prevent abuse.

For display the templates check if a photo path exists and if so, render an `<img>` tag with that path. Photos on posts appear in the feed, and party flyers appear as prominent header images on party cards and detail pages. I intentionally only allow photos on posts, not comments, to keep the feed clean and maintain a visual hierarchy where posts are primary content and comments are secondary discussion.

I limited uploads to image types only (png, jpg, gif) to prevent users from uploading executable files, scripts, or other potentially dangerous content. The `secure_filename()` function removes characters that could be used for directory traversal attacks or file system exploits. I implemented file size limits to prevent abuse and manage server storage - someone could otherwise upload gigabyte-sized files and fill up the disk. Storing paths instead of binary data in the database keeps queries fast and lets the web server handle file serving efficiently. The decision to disallow photos in comments was about UX - if every comment could have photos, threads would get visually overwhelming and hard to follow. Posts deserve rich media, comments should stay conversational and text-focused.

# About

# My Wishlist

# Settings

A “design document” for your project in the form of a Markdown file called DESIGN.md that discusses, technically, how you implemented your project and why you made the design decisions you did. Your design document should be at least several paragraphs in length. Whereas your documentation is meant to be a user’s manual, consider your design document your opportunity to give the staff a technical tour of your project underneath its hood.