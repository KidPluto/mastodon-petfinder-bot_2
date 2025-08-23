I was attempting to not have to write, or look at the code, when creating this bot.  I was mostly successful at that. 

The Petfinder API will fail every once and a while.  When that happened I tried looking at the code, until I realized it was just an intermittent thing, it was a problem with the code.

At one point it offered a query for Dogs & Cats, only to afterwards admit only one type of pet could be queried at a time.
It's confusing that it knows the correct value to pass to the API, but only after being challenged.  Why not give me the correct code on the first iteration?

One thing I learned was that Github Actions will run the script on a schedule.  

I find myself constantly arguing with Chatgpt or Copilot.  The latest example being the code to try and reduce the amount of time before reposting the same cat again.  I was given code which would only retrieve 10 cats, and give up if all of them had been posted in the last week.  But the message to log said "No new cats to post this week."  Which was just wrong. In addition the file to track which cats have already been posted is not getting created.

I tell it to regenerate the entire script when giving me new code and to add comments on the new code.  Which it does, and removes all my existing comments.  It's like dealing with a really smart stupid person.  

Copilot says - To fix unresolved imports run in your terminal: "pip install requests Mastodon.py" and will let me select but not copy that text string.  Ugh.


