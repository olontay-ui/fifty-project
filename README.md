# What's The Move Harvard: An On-Campus Social Calendar
Hello, and welcome to our website, WTM Harvard! Have you ever found yourself wondering how you'll spend your free evening, or what parties are going on at campus? Well, you're in luck, because WTM Harvard is our social website where users can post about parties going on.

## What is WTM Harvard?

WTM Harvard is basically like a social but specifically for your Harvard parties and events. We built this website to solve a super common problem, trying to figure out what's happening on campus on any given night. Instead of scrolling through group chats or texting around to find out where the parties are, you can just check WTM Harvard. Anyone can create an account, post about parties they're hosting, browse what's happening and even save parties to a wishlist for later. We also added some really cool features such as a  interactive map that shows you exactly where parties are located around Harvard Square!

The whole site is built using Flask, SQLite (a simple database) and some JavaScript for the interactive features. This project uses a lot of the concepts from CS50 like databases, user authentication and file uploads, and APIs. 

## The Main Features 

### Make an Account and Log In

You need to create an account to do most things on the site. When you register, you'll pick an email, create a password, and choose a username. Your password gets "hashed" before we save it, which basically means it gets scrambled up so that even if someone looked at our database they couldn't see your actual password. 

Once you're logged in, the website remembers you're logged in even when you click around to different pages, session managament. Flask keeps track of who you are so you don't have to log in every single time you visit a new page. If you want to change your username later, you can go to the Settings page and pick a new one. Your login email stays the same though.

### Creating and Managing Parties

If you're hosting a party, you can create a listing for it. Just click "Add New Party" and fill out a form with the basics: party name, your name as the host, where it's happening, what day, what time, and optionally a description where you can add extra details like "bring your own drinks" or "costume required" or whatever people need to know.

When you create a party, the host name you type in has to match your username. This prevents people from creating fake parties and saying someone else is hosting.

Once you create a party, it shows up on the main parties list for everyone to see. The website automatically only shows parties that haven't happened yet. Everything is sorted by date and time with the soonest parties at the top. That way people can see what's happening tonight or this weekend without having to scroll through old stuff.

If you need to change any details about your party (like the time changes or you want to update the description), you can edit it anytime. Just go to your party's page and click "Edit Party." You can also delete it completely if the party gets cancelled. Don't worry though only YOU can edit or delete YOUR parties. Other people can't mess with your listings.

### The Social Feed

Beyond just listing parties, we wanted WTM Harvard to feel social and interactive. That's where the feed comes in! Think of it like a Twitter or Instagram feed but focused on the Harvard social scene. Anyone can post updates, thoughts, questions, or whatever they would like. 

All the posts show up in order with the newest ones first, so you're always seeing the most recent stuff. Each post shows who wrote it and when, so you know what's current. Ppeople can also comment on posts! So if someone asks "what's the move tonight?" people can reply with suggestions or info. It becomes a conversation.

You can click on any post to see it in more detail along with all its comments. Comments are shown oldest-to-newest so you can follow the conversation in order. And just like with parties, you can delete your own posts and comments if you change your mind about what you wrote. The feed also shows you how many comments each post has, so you can tell at a glance which posts have started discussions. It's a nice way to see what people are actually engaging with.

### The Wishlist Feature

You can save any party to your personal wishlist with one click so you just click the heart button on any party. The heart fills in to show it's saved. All your saved parties live on your wishlist page where you can review them whenever you want. This is super helpful when you're trying to decide between multiple parties on the same night, or when you want to plan your weekend in advance. Everything you need to know about each party is right there on your wishlist, the name, host, location, time, description, flyer, everything.

If you change your mind about a party, just click the heart again and it removes it from your wishlist. Your wishlist is personal to you, other people can't see what you've saved, and saving a party doesn't notify the host or anything. It's just a way to bookmark events that interest you. The data saves in our database, so your wishlist is still there even if you log out and come back later.

## Other Interactive Features

We added four major new features based on what we learned in CS50 about web development. These features are what make our site stand out and actually feel modern and useful!

### The Interactive Map

When you go to the parties list page, at the very top there's an interactive map of Harvard Square showing exactly where all the upcoming parties are happening. Each party shows up as a little marker pin on the map, and you can click on any pin to see a popup with info about that party.

We use Leaflet.js, which is a free tool that makes it easy to add maps to websites. The map tiles (the actual map images) come from OpenStreetMap, which is like a free, community made version of Google Maps. When the page loads, some JavaScript code fetches data about all the parties from our database and puts a marker on the map for each one.

When you type "Quincy House" as a location, the computer doesn't automatically know where that is. So we created a big list in our code that matches Harvard location names to their coordinates. We included all twelve undergraduate houses, major buildings like the Science Center and Widener Library, and common spots like Harvard Square. When you create a party at "Lowell House," our code looks up Lowell House in the list and finds its coordinates, then saves those numbers in the database along with your party info.

What if you type in a location that's not in our list? The system just defaults to putting it in the middle of Harvard Square. It's not perfect, but it's better than nothing! In the future, we could connect to a real geocoding service (like Google Maps API) that knows every address, but those usually cost money or have limits on how many times you can use them per day.

The map talks to our database through something called an API endpoint. We created a special URL (`/api/parties/map`) that, when accessed, sends back party data in JSON format. JSON is just a way to structure data that JavaScript can easily read. So the JavaScript in the page asks that URL "hey, give me all the party data," gets back a nice organized list, and then creates a marker for each party. This separation of getting data vs. displaying data is a best practice in web development that we learned about in CS50.

### Host Verification (Security Feature)

This feature is all about trust and security. The problem we're trying to solve is: how do you know a party listing is actually from the person hosting the party? Our solution is simple but effective: when you create a party, the "host name" you type in MUST match your username. The website checks this on the server and if the names don't match, it won't let you create the party. You'll see an error message like "Host name must match your username (YourUsername) to verify you are the actual host."

Once a party passes this verification check, we show a little green badge next to the host name that says "✓ Verified Host." This gives other users confidence that the party is legit and actually from the person listed. Every party in our system is verified because you have to be logged in to create parties and the host name has to match. We made the checking case-insensitive. This makes it more user-friendly without sacrificing security. The check happens every time you create OR edit a party, so you can't sneak around it by editing an existing party later.

This feature uses concepts from the SQL and Flask sections of CS50. We query the database securely (using something called parameterized queries that prevent hacking attempts) and we do all the validation on the server where users can't mess with it.

### Photo Uploads for Posts

We added the ability to attach photos to your posts on the feed. When you're creating a post, you'll see a field that says "Add Photo (Optional)" with a button to choose a file. You can upload PNG, JPG, or GIF files (the most common image types). The "optional" part is important - you don't HAVE to add a photo to every post. 

First, the form has to have a special attribute (`enctype="multipart/form-data"`). When you hit submit, the photo gets sent to our Flask server along with your post text. The server then does a bunch of safety checks. It makes sure you actually uploaded a file, checks that the file extension is one we allow and uses a function called `secure_filename()` to clean up the filename and remove any weird characters that could cause problems. Then, to avoid conflicts, we add a timestamp to the beginning of the filename. 

The photo gets saved in a folder on our server (`static/uploads/posts/`), and we save the path to that photo in our database alongside your post content. When someone views the feed, the website checks if each post has a photo and, if it does, displays it right there in the feed. The photos are set to automatically resize so they don't break the page layout on phones or computers.

We ONLY allow photos on posts, not on comments. Posts are the main content, so they deserve rich media. But if every comment could have a photo, the page would get super cluttered and messy. Comments are meant to be quick responses and discussions. This isn't just a UI decision - we made sure the comment form doesn't have a photo upload field, AND the server-side code for creating comments doesn't process any uploaded files. So there's no way to sneak photos into comments. There's also a file size limit of 16MB per upload so it keeps people from uploading giant files that would take forever to load.

### Party Flyer Uploads

Similar to post photos, we also let party hosts upload flyers for their events! This is super useful because a lot of parties have custom-designed flyers that show off the theme, list special guests or DJs, show dress codes with pictures, or just look really cool and make people want to come. When you're creating or editing a party, there's a field near the bottom that says "Party Flyer/Photo (Optional)" where you can upload an image. Just like with post photos, you can use PNG, JPG, or GIF files up to 16MB. 

The technical process for flyer uploads is almost identical to post photos. The file gets validated, the filename gets sanitized and timestamped, and it gets saved to a folder (`static/uploads/parties/`). The path to the flyer gets saved in the party's database record. If you edit a party later and upload a new flyer, it updates to the new one. Both the photo upload features (posts and flyers) demonstrate important concepts from CS50 Week 9 about handling file uploads in Flask, validating and securing uploaded files, and storing/serving static media files. Plus they show good design thinking about WHEN and WHERE to allow visual content to enhance the user experience without making things messy.

## How to Get This Running on Your Computer
First, you need Python installed on your computer. We need version 3.7 or newer. To check if you have it, open your terminal (or command prompt on Windows) and type: python3 --version.

Next download or clone this project to your computer. You should have a folder with all the files - the `app.py` file, a `templates` folder, a `static` folder, etc.

Then open your terminal and navigate to the project folder (use `cd` command to change directories). Then type: pip install Flask werkzeug. Since our website uses SQLite, which is a simple database that stores everything in one file. We need to create this file and set up all the tables (kind of like spreadsheets) that store our data.

Finally, time to start the server! Type:
```
python3 app.py
```

You should see some text appear saying the server is running. It'll show you a URL.

## How to Use the Website

Now that it's running, here's what you can do:

**Making an Account**: Click "Log In" at the top right, then click the link to register instead. Fill in an email, password, and username. Hit register and you're in!

**Looking at Parties**: Click "Parties" in the menu at the top. You'll see the map first, then scroll down to see all the party cards. Each card shows the party name, who's hosting, where it is, when it is, and any description or flyer they added. Click "View Details" to see the full page for any party.

**Creating Your Own Party**: On the parties page, click "Add New Party" (you have to be logged in). Fill out the form - remember, the host name MUST be your username! You can upload a flyer if you want. Click "Save party" and boom, your party is live!

**Saving Parties You Like**: See a party that looks cool? Click the heart button to add it to your wishlist. You can see all your saved parties by clicking "Wishlist" in the menu.

**Using the Feed**: Click "Feed" in the menu. You'll see everyone's posts. If you're logged in, there's a form at the top where you can write your own post and add a photo if you want. Click any post to see it with all its comments, and add your own comment at the bottom.

**Changing Your Username**: Click "Settings" in the menu (when logged in). You can change your display name here if you want to go by something different.

**Editing or Deleting Your Stuff**: If you created a party, post, or comment, you'll see edit/delete buttons on it. Only you can change or delete your own stuff, so don't worry about other people messing with your content.

