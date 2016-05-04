# statshark
##Objective

Develop data driven NFL wagering strategies 

##Elevator Pitch

* Do you wager on NFL games?

* Have you ever wondered if the underdog typically beats the spread in the wild card round?

* Have you pondered whether Minnesota Vikings home games typically beat the over under in December?

* Does your life depend on how the New England Patriots have faired against the spread, on ther road, in the last 5 years, when the temperature is > 60 degrees and the opponent is below .500?

Then you will find this application useful, and you may even want to pull the code and modify it!

##Overview

The project is currently hosted here:

http://statshark.joshyg.com/

And the following link provides a step by step example of how the application is used to query nfl data:

http://statshark.joshyg.com/about/

The data is primarily combed from nfl.com and http://www.pro-football-reference.com/. I used a few other sources for the spread data.

The data goes back to the NFL-AFL merger.  The old stuff is fun to look at, but its usually more useful and insightful to limit your results to the last 10-15 years.

If you want to pull this application you will have to run the parser to populate the db, which is located in:

support_files/superscript.py

Note that the support script uses the django ORM to write to the database.  You will have to pull the entire repo and run python manage.py migrate in the project root in order to initialize the database.

##Current Issues

The documentation must be improved, specifically I must add usage info for superscript.py.

The backend is still on sqlite, which sometimes barfs when you run a very complex query.

This is a long term personal project that I have used with friends for several years, and Im only now starting to make my stuff public (hmm I wonder why? If you have a guess dont tell my boss)

If you find other issues feel free to send me an email at joshgrossberg@gmail.com

##Disclaimer

cairoplot is not my code.  I pulled it from here: http://cairoplot.sourceforge.net/
