This is my script to web scrape the kijiji.ca website for any new items im looking for.<br><br>
I store the kijiji web pages of items I want to be updated on new items for on my postgres database.
I also store key words I dont want new messages for.

Basic Structure of the script:<br>
LOOP
  - connects to my postgres database and gets latest kijiji links
  - randomizes links
      - so kijiji doesnt detect the script
  - connects to db and gets rejected terms
  
  - scrapes each link for:
      - title
      - location
      - description
      - price
      - link
  - check if item is a new item
      - if it is it stores it in a dictionary
      - sends it to telegram
  - rejects item if its a sponsord item
  
  - at 4:30am clear out the dictionary
      - so that dictionary doesnt get too large and bogs down the script
    
  - dont send telegram message on first pass so that after clearing out the dictionary
   at 430am you get alot of new item messages
 
