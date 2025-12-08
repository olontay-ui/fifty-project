# Design for What's The Move Harvard: A Breakdown of Choices

Welcome to WTM Harvard! Our website is made by students for students to find all of the best parties and social events going on at Harvard and the greater Cambridge-Allston area. Designed with your ease in mind, WTM Harvard is easy to navigate and interact with. Additionally, it is meant to be another social platform for Harvard students, where we can all keep each other in the loop and outside of our studies now and then. Below is each design feature of WTM Harvard's website, as well as the thought process that went behind implementing each.

# Home
The home page is where users land upon arriving on our website. It includes a few tables of fluff and infomation on how to use our website. The first div has a cool feature that directly reports parties posted previously. Users can click on them with a redirect to detailed party views through `href`. Users can also see all parties with a similar redirect.

# Register/Login
The register/login function works essentially the same way as it does in the finance pset - indeed, we took great design inspiration from that work. We store users' usernames in a sql database called `wtm.db` in a table called `users`, included pre-initialized as a part of the program. Their emails and hashed passwords are stored in the database and are used for authentication upon login.

# Parties
The parties page is the soul of our project. On this page, we essentially display the user a list of parties in a Jinja based HTML script. Within the table, we show the users very useful information for if they want to party. This includes the parties's name, the organizer, and location of the party. Essentially, the way we sort of the information is through quite simple SQL data base that we initiated within our own code base that carries onto the server.

## Add party
The way you add parties to the party tracker is through the specific add party function. The add party function only works when you're logged in; we check this through Flask's session function. If not logged in, users will be prompted to log in through a redirect to the login page. 

## Detailed View
When a party is clicked on, a detailed view of all the party information comes up. This is done through a redirect and a seperate template for the party detailed view. A cool feature of this detailed view is `edit` and `delete`, where users, if on a detailed view of *a party they created*, can edit and delete the party. 

## Interactive Party Map

The interactive map required four main pieces: storing coordinates in the database, converting location names to coordinates, creating an API to send party data, and using JavaScript to draw the map. I added `latitude` and `longitude` columns to the parties table.

For geocoding (converting "Lowell House" to GPS coordinates), I created a Python dictionary called `HARVARD_SQUARE_LOCATIONS` that maps location names to coordinate pairs. I manually looked up coordinates for all the houses, major buildings, and common spots on Google Maps. The `geocode_location()` function does case-insensitive partial matching, so "Lowell," "lowell house," and "LOWELL HOUSE" all match. If no match is found, it defaults to Harvard Square coordinates.

I made an API endpoint at `/api/parties/map` that returns party data in JSON format. The SQL query joins parties with users (to get verified host names), filters for upcoming parties with valid coordinates, and returns everything as JSON. This separates data retrieval from display, and the JavaScript just asks the API for data and the API handles all the database stuff.

For the actual map I used Leaflet.js with OpenStreetMap tiles. The JavaScript creates a map centered on Harvard Square, fetches party data from my API, and loops through each party to create markers. Each marker has a popup showing party details. The `fetch()` function is asynchronous, meaning it doesn't freeze the page while waiting for data.

I chose a custom location dictionary over Google Maps API because: (1) Google costs money after you hit usage limits, (2) I don't depend on external services, and (3) for Harvard-specific locations, my curated list is actually more accurate. The tradeoff is it only works for predefined locations, but Harvard parties mostly happen at known spots anyway. I separated the API from the display so the data could be reused elsewhere and each piece of code does one job cleanly. I only show upcoming parties to keep the map relevant and performant.

## Host Verification Security System

The verification system akes sure that party creators are actually the hosts by requiring the host name to match the logged-in user's username. When someone submits the party form, my Flask route queries the database to get the current user's `display_name`, then compares it to the submitted `host_name` using case-insensitive matching (`.lower()` on both strings). If they don't match, I return an error page showing what their actual username is. This check happens on every party creation AND edit, preventing someone from creating a party correctly then editing it to change the host later.

I use parameterized SQL queries (`SELECT display_name FROM users WHERE id = ?`) instead of string concatenation to prevent SQL injection attacks. The `?` placeholder gets safely replaced with the actual value by the database library. I pre-fill the host name field with the user's username in the template to make the form easier and hint at the requirement. The error message explicitly shows their username so they know exactly what to type.

On the frontend, I display a green "✓ Verified Host" badge on all parties. Since parties can only be created by authenticated users whose host names match their usernames, every party is inherently verified. The badge builds trust and shows users the system is working.

I implemented this serverside instead of clientside because clientside JavaScript can be bypassed by anyone who opens browser dev tools. Serverside validation is authoritative - it controls what gets saved to the database. The tradeoff is less flexibility (you can't create parties on behalf of groups or other people), but I decided authenticity and trust were more important than convenience. Case insensitive matching (`kelly` = `Kelly`) is userfriendly without compromising any of the security since usernames aren't case sensitive anyway. Pre filling the host name field improves UX while the error message with the actual username prevents frustration from users who don't remember their exact username.

# Feed

## Live community feed

The live community feed is an important feature that allows users to not only create posts and comments, but to respond to other posts and comments in the feed. As for the database structure of the feed, there are two tables stored under wtm.db: posts, and comments. Posts stores the user's post with its id, content, any photos, and a timestamp. Comments stores a user's comment with its id, content, and link to a post_id. Both tables refer to the users table in wtm.db and include an ON DELETE CASCADE so that when a post is deleted, its associated comments are also deleted.

When a user wants to create a post, they can submit a text with maximum 1000 characters and an optional photo through a form made with HTML. The system authenticates that the post is coming from the logged-in user, as well as handles file uploads securly with a name and a timestamp, and then inserts the post into the wtm.db database, which are stored in static/uploads/posts.

When a user wants to view a post(s), the "Feed" tab at the top of the website allows users to see all posts and associated comments. This page queries all posts with JOIN operations, which allows us to see the username of the poster to the post as well. There are comment counts displayed, which are displayed in descending creation time order.

When a user wants to add a comment, they can click on an individual post and submit a comment that is up to 500 characters maximum. The program ensures that the user and the post exist before adding the comment to the feed and wtm.db. Comments don't support photo uploads like posts.

Only the creator of a post or comment can delete their own post or comment. Delete buttons are shown in each to provide users this option. This is done by checking session.get('user_id') against the content's user_id.

## Photo Upload System (Posts and Party Flyers)

The photo upload system works the same way for both feed posts and party flyers, I just implemented it in two different routes. I added `photo_path TEXT` to the posts table and `flyer_path TEXT` to the parties table to store file paths (like "uploads/posts/20251207_183045_photo.jpg"). I store paths instead of the actual image data because file systems are better at serving files while databases are better at querying data. The paths are relative to the `static` directory which Flask automatically serves.

I configured upload settings in `app.py`, an upload folder location, allowed extensions (png, jpg, jpeg, gif only), and a 16MB max file size. The HTML forms need `enctype="multipart/form-data"` or file uploads won't work - this tells the browser to send file data in a special format. When a file is uploaded, I check if it exists, validate the extension with `allowed_file()`, sanitize the filename with `secure_filename()` to prevent malicious filenames like "../../hack.jpg", prepend a timestamp to make it unique, save it to the appropriate folder, and store the path in the database.

The timestamp prepending is crucial for preventing filename conflicts. If two users both upload "party.jpg," the second would overwrite the first without timestamps. By adding the date and time like "20251207_183045_party.jpg," every file is guaranteed to be unique. I chose 16MB as the max size because it's big enough for high-quality smartphone photos but small enough to prevent abuse.

For display the templates check if a photo path exists and if so, render an `<img>` tag with that path. Photos on posts appear in the feed, and party flyers appear as prominent header images on party cards and detail pages. I intentionally only allow photos on posts, not comments, to keep the feed clean and maintain a visual hierarchy where posts are primary content and comments are secondary discussion.

I limited uploads to image types only (png, jpg, gif) to prevent users from uploading executable files, scripts, or other potentially dangerous content. The `secure_filename()` function removes characters that could be used for directory traversal attacks or file system exploits. I implemented file size limits to prevent abuse and manage server storage - someone could otherwise upload gigabyte-sized files and fill up the disk. Storing paths instead of binary data in the database keeps queries fast and lets the web server handle file serving efficiently. The decision to disallow photos in comments was about UX - if every comment could have photos, threads would get visually overwhelming and hard to follow. Posts deserve rich media, comments should stay conversational and text-focused.

# About
The about file is just a classic point for any software project. In this part of the webpage, we just have a quick description of what the motivation behind the project was and how to use it.

# My Wishlist

The wishlist feature gives users the ability to save parties that they are interested in attending, which allows for users to personalize a collection of interesting parties. A user can access their wishlist when logged in by clicking on the "My Wishlist" tab at the top of the page.

A table titled "wishlist" was created in wtm.db that allows for many interactions between the users and parties table. This table links user_id and party_id with a UNIQUE constraint so that duplicates are avoided. added_at is a timestamp in the wishlist table so that all times a user adds or toggles their wishlist is tracked and saved. An ON DELETE CASCADE is used when a user deletes a party that they created, which will in turn delete the same party in a user's wishlist if they added it.

One can toggle their wishlist using the /party/<party_id>/wishlist endpoint. This allows adding and removing of parties, as well as checks if entries to the wishlist exist. The endpoint returns JSON, which indicates whether the action the user takes was completed, such as telling the user if an item was added or removed from their wishlist.

get_user_wishlist_ids() is a function defined in app.py that retrieves party IDs in the user's wishlist, which are passed to the template and rendered conditionally with red heart emoji (❤️) if a user added that party to their wishlist, and a white heart emoji (🤍) if that party is unsaved in a user's wishlist.

The /wishlist route joins all three tables of wishlist, parties, and users so that all of the party details added to a wishlist are displayed and in descending order. In the case that a wishlist is empty or a user doesn't have any saved parties, the wishlist shows a message that has an embedded link to browse the parties page of all parties.

The features in list.html appear on the user's end in showing hte heart button by a party so that a user may add this party to their wishlist. Clicking on the button triggers a fetch POST to the toggle endpointm which then updates the emoji color based on whether the user adds or removes a party from their wishlist. wishlist.html allows a seamless removal of parties from the wishlist that refreshes the page automtically when the user removes a party. When a user removes a party, a warning message is first displayed to confirm the action.

Essentially, the wishlist is an entirely private and personalized aspect of WTM Harvard for users.

# Settings

The settings feature provides users the ability to update their display username, whilst maintaining their login information and consistency across the entire website. As usernames are displayed in various aspects of the website (when a user creates a party, post, and logs in), a user has the ability to change their username, as it is displayed to other users on the site.

/settings allows GET and POST requests, where on a GET request, the user's current display_name from users in wtm,db is shown. It's shown in the form box in settings. When using POST, the new username is validating assuing it exists and that it satisfies the following criteria:

- Length: 3-20 characters
- Characters: letters, numbers, and underscores only
- Uniqueness: the username must not already exist in the users table in wtm.db
- Non-empty: the username cannot be blank

If all of these criteria are satisfied, then the user is allowed to change their name in settings. The user's username is then updated in users, and the session is immediately updated as to allow the new username ot be view across the website.

Some security considerations made in settings are that the email cannot be changed through settings, which prevents users from locking themselves out. Also, it ensures stable authentication and that there is one account linked to each email address. The email is displayed in settings as read-only in the template. Users do not have to log out and log back in when their username is updated, as the session is updated after the change is made.

If a user does not satisfy the criteria when creating their username, the exact error message is displayed, and will repeat until the username satisfies the criteria. There is also a cancel button provided in the case a user changes their mind.
