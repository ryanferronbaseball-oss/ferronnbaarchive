/* Museum game-gallery nominations. Only approved stories are published as full exhibits. */
(()=>{'use strict';
const candidates=[
 ['2007-03-18','Minnesota Timberwolves','Los Angeles Lakers','NBA'],
 ['2008-01-27','Cleveland Cavaliers','Los Angeles Lakers','NBA'],
 ['2008-12-06','Utah Jazz','Phoenix Suns','NBA'],
 ['2010-11-22','New Orleans Hornets','Los Angeles Clippers','NBA'],
 ['2018-02-03',"Saint Mary's",'San Diego','College Basketball'],
 ['2019-02-20','Nevada','San Diego State','College Basketball'],
 ['2019-11-30','Eastern Michigan','UC Irvine','College Basketball'],
 ['2022-11-17','Utah State','San Diego','College Basketball'],
 ['2007-11-25','San Francisco 49ers','Arizona Cardinals','NFL'],
 ['2018-11-10','Davidson','San Diego','College Football'],
 ['2003-07-24','Colorado Rockies','Los Angeles Dodgers','MLB'],
 ['2006-06-28','Atlanta Braves','New York Yankees','MLB'],
 ['2012-04-06','Kansas City Royals','Los Angeles Angels','MLB'],
 ['2013-08-09','Tampa Bay Rays','Los Angeles Dodgers','MLB'],
 ['2018-09-28','Arizona Diamondbacks','San Diego Padres','MLB'],
 ['2022-10-18','Philadelphia Phillies','San Diego Padres','MLB'],
 ['2018-02-17','California','San Diego','College Baseball'],
 ['2019-02-22','Oklahoma','San Diego','College Baseball'],
 ['2020-02-28','Monmouth','San Diego','College Baseball'],
 ['2022-03-05','Dallas Baptist','San Diego','College Baseball'],
 ['2022-05-28','San Diego','Gonzaga','College Baseball','neutral'],
 ['2022-06-03','San Diego','Vanderbilt','College Baseball','neutral'],
 ['2024-02-23','Iowa','Auburn','College Baseball','neutral'],
 ['2025-05-16','Oregon','Iowa','College Baseball'],
 ['2025-05-23','Texas A&M','LSU','College Baseball','neutral'],
 ['2026-04-05','LSU','Tennessee','College Baseball'],
 ['2026-05-16','Arkansas','Kentucky','College Baseball']
].map(([date,away,home,sport,site])=>({date,away,home,sport,site}));
const stories={
 '2012-04-06':{
  title:'A New Era in Anaheim: Pujols’ Debut and Weaver’s Masterpiece',
  score:'Los Angeles Angels 5 · Kansas City Royals 0',
  venue:'Angel Stadium · Anaheim, California · Opening Day',
  image:'./pujols-angels-opening-day-2012.webp',
  photoAlt:'Albert Pujols batting in his white number 5 Los Angeles Angels uniform',
  caption:'APRIL 6, 2012 · ROYALS AT ANGELS · PUJOLS DEBUT',
  game:'../mlb/index.html',
  paragraphs:[
   'Opening Day 2012 marked the beginning of a new era in Anaheim. After 11 legendary seasons with the St. Louis Cardinals, Albert Pujols made his regular-season debut for the Angels in front of 44,106 fans.',
   'Although Pujols went hitless in his first three at-bats, the night belonged to Angels ace Jered Weaver. He dominated Kansas City over eight shutout innings, allowing four hits, striking out 10, and issuing no walks.',
   'The game remained scoreless through seven innings before the Angels erupted for five runs in the eighth. Peter Bourjos and Torii Hunter delivered RBI singles, and Erick Aybar broke it open with a three-run triple.',
   'Scott Downs finished the shutout, securing a 5–0 Opening Day victory.',
   'For Courtside Archive, this game represents the excitement of Pujols’ highly anticipated Angels debut and a dominant performance from Weaver.'
  ],
  columns:['Player','Performance','Context','Highlight'],
  players:[['Jered Weaver','8 IP · 0 R · 10 K · 0 BB','Opening Day start','Dominant pitching'],['Albert Pujols','Angels regular-season debut','First game with Los Angeles','New era'],['Erick Aybar','Three-run triple','Five-run eighth inning','Broke game open']]
 },

 '2018-02-03':{
  title:'Landale’s 34 and 18: Saint Mary’s survives in San Diego',
  score:'Saint Mary’s 65 · San Diego 62',
  venue:'Jenny Craig Pavilion · San Diego, California',
  image:'./saint-marys-usd-2018-landale-pineiro.webp',
  photoAlt:'Jock Landale defending San Diego forward Isaiah Pineiro',
  caption:'FEBRUARY 3, 2018 · SAINT MARY’S AT SAN DIEGO · LANDALE 34 AND 18',
  game:'../ncaab/index.html',
  paragraphs:[
   'On February 3, 2018, No. 13 Saint Mary’s arrived at the Jenny Craig Pavilion riding one of the longest winning streaks in the country. San Diego pushed the Gaels to the final moments in a memorable West Coast Conference matchup.',
   'Saint Mary’s center Jock Landale delivered a remarkable performance: 34 points, 18 rebounds, and four assists while shooting 15-for-22 from the floor. His interior scoring and rebounding proved decisive in a game where every possession mattered.',
   'San Diego forward Isaiah Pineiro answered with 24 points, keeping the Toreros within striking distance throughout the night. The matchup between Pineiro and Landale highlighted a tense, physical contest.',
   'Saint Mary’s escaped with a 65–62 victory, extending its winning streak to 18 games. For Courtside Archive, the close finish and Landale’s dominant 34-point, 18-rebound double-double made this a standout night at the Jenny Craig Pavilion.'
  ],
  columns:['Player','Performance','Context','Highlight'],
  players:[['Jock Landale','34 points · 18 rebounds · 4 assists','15-for-22 FG','Saint Mary’s'],['Isaiah Pineiro','24 points','San Diego','Kept Toreros close']]
 },

 '2013-08-09':{
  title:'Six Runs Down, One Unforgettable Comeback',
  score:'Los Angeles Dodgers 7 · Tampa Bay Rays 6',
  venue:'Dodger Stadium · Los Angeles, California',
  image:'./dodgers-rays-2013.webp',
  photoAlt:'Los Angeles Dodgers teammates celebrating during the August 9, 2013 comeback',
  caption:'AUGUST 9, 2013 · RAYS AT DODGERS · SIX-RUN COMEBACK',
  game:'../mlb/index.html',
  paragraphs:[
   'August 9, 2013, was a memorable night at Dodger Stadium, with excellent seats for one of the most remarkable comebacks in Courtside Archive history.',
   'The Dodgers were in the middle of an extraordinary second-half surge, energized by rookie sensation Yasiel Puig and a lineup featuring Adrian Gonzalez, Hanley Ramirez, and Andre Ethier. Tampa Bay brought a talented team led by Evan Longoria, Ben Zobrist, Wil Myers, and former Cy Young Award winner David Price.',
   'For much of the evening, the Rays dominated. Price delivered seven strong innings, allowing just one unearned run. Tampa Bay built a 6–0 advantage, with former Dodger James Loney collecting three hits and two RBI.',
   'Los Angeles scored once in the seventh before Puig’s RBI double and Juan Uribe’s run-scoring single cut the deficit to 6–3 in the eighth. In the ninth, Mark Ellis tripled home a run, Nick Punto doubled in another, and Adrian Gonzalez delivered a double to tie the game.',
   'With the winning run at third, Jerry Hairston Jr. hit a ground ball back to Fernando Rodney, whose errant throw into center field allowed Gonzalez to score and complete an improbable 7–6 walk-off victory.',
   'The comeback unfolded before 51,083 fans. For Courtside Archive, this was a special combination of excellent seats, the excitement of Puig’s rookie season, an outstanding collection of talent, and one of the most dramatic finishes witnessed at Dodger Stadium.'
  ],
  columns:['Player','Performance','Context','Highlight'],
  players:[['Yasiel Puig','RBI double','Eighth inning','Rookie sensation'],['Adrian Gonzalez','Game-tying double','Ninth inning','Scored winning run'],['Mark Ellis','RBI triple','Ninth inning','Sparked rally'],['James Loney','3 hits · 2 RBI','Tampa Bay','Former Dodger']]
 },



 '2010-11-22':{
  title:'A ball boy before Lob City: the night the Clippers shocked the Hornets',
  score:'Los Angeles Clippers 99 · New Orleans Hornets 95',
  venue:'STAPLES Center · Los Angeles, California · Pregame ball-boy experience',
  image:'./hornets-clippers-ballboy-2010.webp',
  photoAlt:'Chris Paul in his blue New Orleans Hornets uniform during the Hornets–Clippers matchup',
  caption:'NOVEMBER 22, 2010 · HORNETS AT CLIPPERS · A BALL BOY BEFORE LOB CITY',
  game:'../nba/game.html?id=19',
  paragraphs:[
   'Some games are remembered for a spectacular performance, a dramatic finish, or a championship moment. For Ryan Ferron, November 22, 2010, was memorable for something that happened before the game even began: he got to serve as a pregame ball boy for the Los Angeles Clippers.',
   'That rare opportunity to be involved in the pregame environment at STAPLES Center gave him a different perspective on professional basketball. The personal experience, more than any particular play or box-score number, is what makes this night one of the most meaningful memories in the Courtside Archive.',
   'Looking back, the matchup offered a remarkable glimpse of what was to come. Chris Paul arrived as the visiting superstar point guard of the New Orleans Hornets, more than a year before he would be traded to Los Angeles and team up with Blake Griffin to launch the Clippers’ high-flying Lob City era. On this night, Paul was still wearing New Orleans blue.',
   'Griffin was only 15 games into his NBA career. Selected first overall in the 2009 draft, he had missed the entire 2009–10 season with a knee injury and was now beginning the rookie campaign that would make him one of the league’s most electrifying young stars. He finished with 24 points, 13 rebounds, and four assists.',
   'The matchup was also a stunning contrast in team fortunes. New Orleans entered at 11–1 after opening the season with eight straight wins; the Clippers entered at just 1–13 and had lost nine consecutive games. Yet Los Angeles gave its pregame ball boy a night to remember: Eric Gordon scored 27 points, Griffin powered the interior, and the Clippers upset the Hornets 99–95. David West scored a game-high 30 points for New Orleans, while Paul contributed 14 points and six assists.',
   'The most enduring memory remained the pregame experience itself. But the result added another layer: being a ball boy for a 1–13 team on the very night it beat an 11–1 opponent, with the future Lob City partnership unknowingly sharing the court as adversaries. It was a personal milestone and a fascinating snapshot of the Clippers just before their identity changed.'
  ],
  columns:['PTS','REB','AST','More'],
  players:[['Eric Gordon','27','3','4','Clippers’ leading scorer'],['Blake Griffin','24','13','4','Rookie season · 2 BLK'],['David West','30','10','5','Game-high points'],['Chris Paul','14','4','6','2 STL · future Clipper'],['Al-Farouq Aminu','16','4','—','Clippers reserve'],['DeAndre Jordan','12','8','—','Future Lob City teammate']]
 },
 '2008-12-06':{
  title:'Three quarters tied: a star-studded battle in Phoenix',
  score:'Phoenix Suns 106 · Utah Jazz 104',
  venue:'US Airways Center · Phoenix, Arizona',
  image:'./jazz-suns-shaquille-oneal-2008.webp',
  photoAlt:'Phoenix Suns center Shaquille O’Neal holds the basketball while surveying the floor',
  caption:'DECEMBER 6, 2008 · JAZZ AT SUNS · THREE QUARTERS TIED',
  game:'../nba/game.html?id=15',
  paragraphs:[
   'On December 6, 2008, the Phoenix Suns welcomed the Utah Jazz to US Airways Center for a Western Conference showdown featuring an extraordinary collection of NBA talent. With Shaquille O’Neal, Steve Nash, Amar’e Stoudemire, Deron Williams, and Andrei Kirilenko sharing the court, the game offered an opportunity to witness several defining players of their era.',
   'What made the evening particularly memorable was the remarkably even score. The teams finished the first quarter tied at 26, reached halftime tied at 50, and each scored 28 points in the third. After 36 minutes, the score was still deadlocked at 78–78. Only the final two points separated them.',
   'Despite the star-studded matchup, Phoenix’s Leandro Barbosa led all scorers with 25 points. Amar’e Stoudemire delivered an exceptional performance with 22 points and 20 rebounds, dominating the glass and providing a crucial interior presence. Shaquille O’Neal added 15 points and 10 rebounds despite foul trouble throughout the second half, while veteran playmaker Steve Nash directed the Suns’ offense.',
   'Utah countered with contributions across its lineup. C.J. Miles and Paul Millsap scored 20 points apiece, with Millsap also collecting 12 rebounds. Mehmet Okur had 12 points and 13 rebounds, while Deron Williams orchestrated the offense with 15 points and an outstanding 15 assists. Andrei Kirilenko supplied 17 points off the bench.',
   'With the score close late in the fourth quarter, Boris Diaw converted a free throw with 1:55 remaining to put Phoenix ahead for good, 100–99. Stoudemire followed with a layup and Nash made two key free throws to stretch the lead to five with 20.7 seconds left. Utah refused to surrender: Kirilenko connected on a three-pointer with 15.5 seconds remaining, but the Suns survived the final possessions for a 106–104 victory.',
   'For Courtside Archive, the game combined remarkable star power, a 20-rebound performance from Stoudemire, and a rare score progression that saw the teams tied after every one of the first three quarters. Three quarters tied. Two points separating the teams. An unforgettable collection of basketball talent.'
  ],
  columns:['PTS','REB','AST','More'],
  players:[['Leandro Barbosa','25','—','—','Game-high scoring'],['Amar’e Stoudemire','22','20','—','20-rebound double-double'],['Shaquille O’Neal','15','10','—','Double-double'],['C.J. Miles','20','4','2','4 threes'],['Paul Millsap','20','12','1','Double-double'],['Deron Williams','15','1','15','15 assists'],['Andrei Kirilenko','17','2','1','Key late 3-pointer'],['Mehmet Okur','12','13','1','Double-double']]
 },
 '2008-01-27':{
  title:'A battle of basketball royalty: LeBron vs. Kobe',
  score:'Cleveland Cavaliers 98 · Los Angeles Lakers 95',
  venue:'STAPLES Center · Los Angeles, California',
  image:'./cavaliers-lakers-lebron-kobe-2008.webp',
  photoAlt:'LeBron James in a red Cavaliers uniform guarding Kobe Bryant in a white Lakers uniform at STAPLES Center',
  caption:'JANUARY 27, 2008 · CAVALIERS AT LAKERS · LEBRON VS. KOBE',
  game:'../nba/game.html?id=13',
  paragraphs:[
   'On January 27, 2008, two of the greatest basketball players of all time shared the floor at STAPLES Center in one of the most anticipated individual matchups of the NBA season. Kobe Bryant and the Los Angeles Lakers hosted LeBron James and the Cleveland Cavaliers in a game featuring two superstars at the height of their powers. The matchup delivered everything fans could have hoped for.',
   'LeBron James finished with 41 points, nine rebounds, four assists, and two steals, shooting 16-for-32 from the field. At 23 years old, James was already among the NBA’s most dominant players, combining extraordinary athleticism with an increasingly complete offensive game.',
   'On the other side, Kobe Bryant recorded 33 points, 12 rebounds, and six assists while shooting 10-for-21. Bryant, then 29, was in the middle of what would become his first and only NBA Most Valuable Player season. Together, the two superstars scored 74 points and showed why they were widely considered the premier players of their generation.',
   'The game was tightly contested throughout, featuring 21 lead changes and nine ties. Cleveland carried a 49–40 lead into halftime, but Los Angeles won the third quarter 31–20 to take a 71–69 advantage entering the fourth. The supporting casts contributed too: Zydrunas Ilgauskas had 16 points and 11 rebounds, Larry Hughes added 16 points for Cleveland, and Lamar Odom supplied 14 points and nine rebounds for Los Angeles.',
   'The Lakers stretched their lead to 84–75 with fewer than eight minutes to play. LeBron refused to let Cleveland fade, scoring 14 of his 41 points in the fourth quarter to lead the comeback. With 20.1 seconds remaining, he hit a critical 22-foot jumper over Bryant, putting the Cavaliers ahead. After Kobe missed a late shot near the basket, James made two free throws with nine seconds remaining and the Lakers failed to get another attempt away, sealing Cleveland’s 98–95 victory.',
   'The afternoon included an unusual 12-minute delay in the first quarter when water began dripping near the court from the STAPLES Center ceiling. Yet the enduring memory was the extraordinary battle between two basketball icons. Before their careers became intertwined in debates about basketball greatness, Bryant and James went head-to-head and delivered a genuine classic.',
   'For Courtside Archive, it was an unforgettable opportunity to witness basketball royalty firsthand: 74 combined points, 21 lead changes, a three-point finish, and two legends competing at the top of their games.'
  ],
  columns:['PTS','REB','AST','More'],
  players:[['LeBron James','41','9','4','16-32 FG · 2 STL'],['Kobe Bryant','33','12','6','10-21 FG · double-double'],['Zydrunas Ilgauskas','16','11','3','Double-double'],['Larry Hughes','16','4','4','2 STL · 2 BLK'],['Lamar Odom','14','9','4','—'],['Daniel Gibson','10','2','1','—']]
 },
 '2007-11-25':{
  title:'Frank Gore’s masterpiece and an unbelievable overtime finish',
  score:'San Francisco 49ers 37 · Arizona Cardinals 31 · Overtime',
  venue:'University of Phoenix Stadium · Glendale, Arizona · First NFL game attended',
  image:'./49ers-cardinals-gore-2007.webp',
  photoAlt:'San Francisco 49ers running back Frank Gore carrying the football through Arizona Cardinals defenders',
  caption:'NOVEMBER 25, 2007 · 49ERS AT CARDINALS · FRANK GORE',
  game:'../nfl/game.html?id=nfl-2007-11-25-sf-ari',
  paragraphs:[
   'On November 25, 2007, Courtside Archive’s first NFL game delivered an extraordinary introduction to professional football. The San Francisco 49ers traveled to Arizona to face the Cardinals in a matchup featuring Frank Gore and future Hall of Famers Kurt Warner and Larry Fitzgerald. What followed was an offensive shootout, a spectacular individual performance, and an overtime ending that few could have predicted.',
   'The afternoon belonged to Frank Gore, who carried 21 times for 116 rushing yards and two touchdowns while catching 11 passes for 98 more yards. His 214 yards from scrimmage and 44.4 PPR fantasy points made for one of the Archive’s greatest all-around performances. Gore’s versatility was a preview of the remarkable career that would eventually place him third on the NFL’s all-time rushing list.',
   'Arizona countered with an explosive passing attack led by Kurt Warner, who completed 34 of 48 attempts for 484 yards and two touchdowns. His favorite target was Larry Fitzgerald, who caught nine passes for 156 yards and two scores, including a spectacular 48-yard touchdown to close the first half. Anquan Boldin added six catches for 76 yards.',
   'The lead changed hands repeatedly. San Francisco trailed 21–17 at halftime, then surged back on a 57-yard touchdown pass from Trent Dilfer to Arnaz Battle. Arizona reclaimed a 28–24 lead in the fourth quarter before Gore broke loose for a 35-yard touchdown run with 1:15 left, seemingly delivering a 31–28 49ers victory.',
   'The Cardinals still had an answer. Warner moved Arizona downfield for a Neil Rackers field goal at the end of regulation, tying the game 31–31. In overtime, Rackers initially made what appeared to be the winning kick, only for a delay-of-game penalty to erase it. His next attempt missed, handing San Francisco another chance.',
   'After a 49ers punt pinned Arizona near its own goal line, defensive lineman Ronald Fields sacked Warner in the end zone and forced a fumble. Tully Banta-Cain recovered it for a game-ending defensive touchdown, completing a stunning 37–31 San Francisco victory and snapping the team’s eight-game losing streak.',
   'For the Courtside Archive, this was an unforgettable first taste of the NFL: Gore’s 214-yard masterpiece, Warner’s 484-yard aerial display, two Fitzgerald touchdowns, and a walk-off defensive score in overtime. The first attended NFL game could hardly have packed in more drama.'
  ],
  columns:['Rush / Pass','Rec / Yds','TD','More'],
  players:[['Frank Gore','21 att · 116 yds','11 rec · 98 yds','2 rush','214 scrimmage yds · 44.4 PPR pts'],['Kurt Warner','34/48 · 484 pass yds','—','2 pass','2 INT'],['Larry Fitzgerald','—','9 rec · 156 yds','2 rec','48-yard TD'],['Trent Dilfer','25/39 · 256 pass yds','—','2 pass','0 INT'],['Anquan Boldin','—','6 rec · 76 yds','0','—'],['Arnaz Battle','—','1 rec · 57 yds','1 rec','57-yard TD'],['Tully Banta-Cain','—','—','1 def','OT fumble recovery TD']]
 },
 '2006-06-28':{
  title:'A-Rod’s redemption: a 12th-inning walk-off in the Bronx',
  score:'New York Yankees 4 · Atlanta Braves 3 · 12 innings',
  venue:'Original Yankee Stadium · Bronx, New York',
  image:'./braves-yankees-walkoff-2006.webp',
  photoAlt:'New York Yankees starting pitcher Chien-Ming Wang preparing to deliver a pitch',
  caption:'JUNE 28, 2006 · BRAVES AT YANKEES · A-ROD WALK-OFF',
  game:'../mlb/game.html?id=41109',
  paragraphs:[
   'On June 28, 2006, two of baseball’s most recognizable franchises met at one of the sport’s most historic venues. The Atlanta Braves visited the New York Yankees at the original Yankee Stadium, bringing together an extraordinary collection of established stars, future Hall of Famers, and one of the most dramatic finishes in Courtside Archive history.',
   'The afternoon began with an outstanding pitching matchup between Atlanta’s John Smoltz and New York’s Chien-Ming Wang. Smoltz, already a legendary postseason performer and future Hall of Famer, delivered seven strong innings while allowing just one run. Wang countered with eight innings of two-run baseball, keeping the Yankees within striking distance. Neither starter factored into the decision.',
   'The star power extended well beyond the mound. New York’s lineup featured Derek Jeter, Alex Rodriguez, Jason Giambi, Johnny Damon, and Bernie Williams. Atlanta countered with Chipper Jones, Andruw Jones, Edgar Rentería, Brian McCann, and Jeff Francoeur. The game offered an opportunity to watch some of the defining players of the 2000s sharing the same field.',
   'Atlanta held a 2–1 lead entering the eighth inning, but Jason Giambi launched a solo home run to tie the game. Both teams remained scoreless through the next three innings, sending the contest deep into extra innings.',
   'In the top of the 12th, Marcus Giles broke the deadlock with a solo home run, putting Atlanta ahead 3–2. With the Braves just three outs from victory, the Yankees faced one final opportunity.',
   'After Jason Giambi drew a one-out walk in the bottom of the 12th, Alex Rodriguez stepped to the plate against Jorge Sosa. Rodriguez had been enduring a difficult June, hearing boos from his own fans as his offensive struggles continued. On a 3–1 pitch, Rodriguez launched a two-run walk-off home run to left field, transforming a 3–2 deficit into a stunning 4–3 Yankees victory. The blast was his 16th home run of the season and the 100th of his Yankees career.',
   'The dramatic finish sent the crowd of 54,186 into celebration, capping a nearly four-hour afternoon at one of baseball’s most storied ballparks. For Courtside Archive, the game combined a Smoltz–Wang pitching duel, an extraordinary collection of talent, the atmosphere of the original Yankee Stadium, and an unforgettable walk-off from one of baseball’s biggest stars.'
  ],
  columns:['H-AB / IP','H / HR','RBI / ER','More'],
  players:[['Alex Rodriguez','2-5','HR','3 RBI','1 BB · walk-off HR'],['John Smoltz (P)','7.0 IP','—','1 ER','No decision'],['Chien-Ming Wang (P)','8.0 IP','7 H','2 ER','No decision'],['Jason Giambi','—','HR','1 RBI','12th-inning walk'],['Marcus Giles','—','HR','1 RBI','Go-ahead HR, 12th'],['Ron Villone (P)','—','—','—','Win'],['Jorge Sosa (P)','—','—','—','Loss']]
 },
 '2003-07-24':{
  title:'The Beginning: an 11-inning walk-off starts the Archive',
  score:'Los Angeles Dodgers 1 · Colorado Rockies 0 · 11 innings',
  venue:'Dodger Stadium · Los Angeles, California · First game attended',
  image:'./rockies-dodgers-first-game-2003.webp',
  photoAlt:'Los Angeles Dodgers pitcher Kevin Brown holding a baseball in his throwing motion',
  caption:'JULY 24, 2003 · ROCKIES AT DODGERS · THE BEGINNING',
  game:'../mlb/game.html?id=15785',
  paragraphs:[
   'On July 24, 2003, the first game in what would eventually become Courtside Archive unfolded at Dodger Stadium. What started as an afternoon between the Colorado Rockies and Los Angeles Dodgers became an extraordinary pitching duel, featuring four future Baseball Hall of Famers and a dramatic walk-off finish.',
   'Dodgers ace Kevin Brown was nearly untouchable, working eight scoreless innings while allowing just three hits, walking two, and striking out six. Colorado countered with Shawn Chacon, who matched Brown’s dominance with seven shutout innings of his own. Neither lineup could break through, and the game remained scoreless through nine innings.',
   'Beyond the pitching, the field featured an incredible collection of baseball history. Four future Hall of Famers appeared: Rickey Henderson and Adrián Beltré for Los Angeles, alongside Larry Walker and Todd Helton for Colorado. It was a remarkable collection of talent to witness at the very beginning of the Archive.',
   'The stalemate continued into extra innings before the Dodgers finally broke through in the bottom of the 11th. Alex Cora opened the inning with a single, and Jolbert Cabrera moved him into scoring position with a sacrifice bunt. With one out, Shawn Green delivered the walk-off RBI single up the middle, scoring Cora and giving Los Angeles a dramatic 1–0 victory.',
   'In front of 33,144 fans, the Dodgers celebrated a hard-earned victory after 11 innings and more than three hours of baseball. For Courtside Archive, however, the significance extends far beyond the final score. This was the first chapter of a lifetime spent attending games, witnessing remarkable athletes, and collecting moments worth remembering.',
   'Every Game Has a Story. This is where the first one began.'
  ],
  columns:['H-AB / IP','H','RBI / ER','More'],
  players:[['Kevin Brown (P)','8.0 IP','3 H','0 ER','2 BB · 6 K'],['Shawn Chacon (P)','7.0 IP','—','0 ER','Scoreless start'],['Shawn Green','2 hits','—','1 RBI','Walk-off single'],['Alex Cora','2 hits','—','—','Winning run'],['Paul Shuey (P)','0.1 IP','—','—','Win'],['Javier López (P)','—','—','—','Loss']]
 },
 '2022-06-03':{
  title:'Brycen Mautz leads San Diego to a stunning NCAA Regional upset',
  score:'San Diego 3 · Vanderbilt 2 · NCAA Corvallis Regional',
  venue:'Goss Stadium at Coleman Field · Corvallis, Oregon',
  image:'./san-diego-vanderbilt-regional-2022.webp',
  photoAlt:'San Diego baseball players celebrate together on the field at Goss Stadium following the Vanderbilt upset',
  caption:'JUNE 3, 2022 · SAN DIEGO VS. VANDERBILT · CORVALLIS REGIONAL',
  game:'../college-baseball/game.html?id=cb-2022-06-03-san-diego-vanderbilt-att0172',
  paragraphs:[
   'June 3, 2022, delivered one of the most significant victories in the University of San Diego’s recent baseball history, as the Toreros stunned perennial national powerhouse Vanderbilt with a 3–2 victory in the opening game of the NCAA Corvallis Regional at Goss Stadium.',
   'At the center of the upset was sophomore left-hander Brycen Mautz, who produced one of the most memorable postseason pitching performances in the Courtside Archive. Facing an accomplished Vanderbilt lineup, Mautz worked seven outstanding innings, surrendering just four hits, one earned run, and one walk while striking out five. Remarkably, he needed only 75 pitches to navigate seven innings, earning his tenth victory of the season.',
   'San Diego provided its starter with an early advantage. Caleb Ricketts drove in Cody Jefferis in the first inning before adding an RBI single in the third to give USD a 2–0 lead. Camden Vasquez extended the advantage to three runs with an RBI groundout in the fourth, putting the Toreros in position for a major postseason upset.',
   'Vanderbilt refused to go away quietly. Dominic Keegan launched a solo home run in the seventh inning, and Calvin Hewett followed with another solo shot in the eighth to narrow the deficit to 3–2. With the pressure mounting, San Diego turned to Ian Churchill in the ninth. Despite allowing the tying run to reach scoring position, Churchill secured the final out and preserved the victory.',
   'The win represented San Diego’s first NCAA Regional victory since 2013, when a Toreros team led by Kris Bryant defeated Cal Poly. Nearly a decade later, Mautz and the 2022 Toreros delivered another memorable postseason moment.',
   'For the Courtside Archive, this game stands as a defining example of a tremendous pitching performance producing an unlikely postseason victory. Against one of college baseball’s most recognizable programs, San Diego demonstrated its ability to compete with the nation’s best, creating an unforgettable afternoon in Corvallis.'
  ],
  columns:['H-AB / IP','Extra / H','RBI / ER','More'],
  players:[['Brycen Mautz (P)','7.0 IP','4 H','1 ER','1 BB · 5 K · Win'],['Caleb Ricketts','1-4','—','2 RBI','—'],['Dustin Allen','2-4','3B','0','1 run'],['Jack Costello','1-4','2B','0','1 run'],['Ian Churchill (P)','1.0 IP','0 H','0 ER','Save'],['Dominic Keegan','1-4','HR','1 RBI','—']]
 },
 '2022-11-17':{
  title:'Eric Williams Jr. scores a school-record 43 in an overtime thriller',
  score:'Utah State 91 · San Diego 89 · Overtime',
  venue:'Jenny Craig Pavilion · San Diego, California',
  image:'./utah-state-san-diego-2022.webp',
  photoAlt:'San Diego forward Eric Williams Jr., number 50, celebrating with his teammates during the Utah State game',
  caption:'NOVEMBER 17, 2022 · UTAH STATE AT SAN DIEGO · ERIC WILLIAMS JR.',
  game:'../college/game.html?id=59',
  paragraphs:[
   'November 17, 2022, produced one of the greatest individual basketball performances in Courtside Archive history, as San Diego’s Eric Williams Jr. scored a school-record 43 points in a thrilling 91–89 overtime loss to Utah State at Jenny Craig Pavilion.',
   'Williams Jr. delivered an extraordinary offensive performance, shooting 13-for-20 from the field, 7-for-8 from three-point range, and 10-for-13 at the free-throw line. He also collected 13 rebounds, recording a remarkable 43-point double-double. His scoring total surpassed the previous San Diego single-game record of 40 points, established by Robert “Pinky” Smith in 1972.',
   'The game itself was a back-and-forth battle featuring 15 lead changes and 10 ties. San Diego jumped to an early 9–0 advantage, but Utah State responded to keep the contest close throughout the evening. With the Toreros trailing in the closing seconds of regulation, Williams Jr. hit a spectacular fadeaway three-pointer from the corner with 2.8 seconds remaining, tying the game at 78 and forcing overtime.',
   'Williams continued his historic night with another three-pointer in the extra period, securing the program scoring record. San Diego’s Marcellus Earlington converted a three-point play with 17 seconds remaining to tie the game at 89, but Utah State’s Steven Ashworth answered with the winning jumper with four seconds left. A final attempt by Sigu Sisoho Jawara missed, sealing a dramatic 91–89 Aggies victory.',
   'Utah State received outstanding contributions from Daniel Akin, who finished with 21 points and 15 rebounds, along with Taylor Funk and Max Shulga, who each scored 20 points. Nevertheless, the night belonged to Williams Jr., whose historic scoring performance and unforgettable game-tying shot made this one of the defining college basketball experiences of the Archive.'
  ],
  columns:['PTS','REB','AST','More'],
  players:[['Eric Williams Jr.','43','13','1','7-for-8 3PT · school record'],['Daniel Akin','21','15','0','7-for-11 FG'],['Taylor Funk','20','6','1','5 threes'],['Max Shulga','20','4','5','5-for-5 3PT'],['Sigu Sisoho Jawara','17','3','3','3 threes']]
 },
 '2022-10-18':{
  title:'An October first and Schwarber’s 488-foot blast',
  score:'Philadelphia Phillies 2 · San Diego Padres 0 · NLCS Game 1',
  venue:'Petco Park · San Diego, California · First MLB postseason game attended',
  image:'./phillies-padres-nlcs-2022.webp',
  photoAlt:'Kyle Schwarber follows through on a swing before a packed Petco Park crowd during the 2022 NLCS',
  caption:'OCTOBER 18, 2022 · PHILLIES AT PADRES · NLCS GAME 1',
  game:'../mlb/game.html?id=715731',
  paragraphs:[
   'October 18, 2022, marked a milestone in the Courtside Archive: the first Major League Baseball postseason game attended. With the San Diego Padres hosting the Philadelphia Phillies in Game 1 of the National League Championship Series, Petco Park provided the setting for an unforgettable evening featuring two outstanding starting pitchers and one of the most extraordinary home runs in postseason history.',
   'The game developed into a remarkable pitching duel between Philadelphia’s Zack Wheeler and San Diego’s Yu Darvish. Wheeler was nearly unhittable, throwing seven shutout innings while allowing just one hit and one walk and striking out eight. Darvish was similarly effective, surrendering only three hits and two runs over seven innings while recording seven strikeouts. Neither offense found much success against the opposing starter.',
   'Philadelphia’s first breakthrough came in the fourth inning when Bryce Harper launched a solo home run to left field, giving the Phillies a 1–0 advantage. Two innings later, Kyle Schwarber delivered the moment that would define the evening. Facing Darvish in the sixth, Schwarber crushed a towering solo home run into the upper deck in right field. The ball left his bat at 119.7 mph and traveled a Statcast-projected 488 feet, becoming the longest home run recorded at Petco Park during the Statcast era.',
   'The two home runs accounted for all of Philadelphia’s scoring. Wheeler and the Phillies bullpen combined to limit San Diego to a single hit, securing a 2–0 victory and a 1–0 series advantage.',
   'For the Courtside Archive, this game holds special significance beyond the final score. The first experience of October baseball at the major-league level featured an exceptional duel between two accomplished pitchers, a home run from Bryce Harper, and a historic display of power from Kyle Schwarber. It was a fitting introduction to the atmosphere and intensity of the MLB postseason.'
  ],
  columns:['H-AB / IP','HR / H','RBI / ER','BB / K'],
  players:[['Zack Wheeler (P)','7.0 IP','1 H','0 ER','1 BB · 8 K'],['Yu Darvish (P)','7.0 IP','3 H','2 ER','1 BB · 7 K'],['Kyle Schwarber','2-3','1','1','1 BB'],['Bryce Harper','1-4','1','1','—']]
 },
 '2024-02-23':{
  title:'A late-night showcase of triple-digit velocity and Auburn’s comeback',
  score:'Auburn 7 · Iowa 5',
  venue:'121 Financial Ballpark · Jacksonville, Florida · Jax College Baseball Classic',
  image:'./iowa-auburn-2024.webp',
  photoAlt:'Iowa baseball players huddle on the field beneath the lights during the late-night February 23, 2024 game',
  caption:'FEBRUARY 23, 2024 · IOWA VS. AUBURN · FIRST PITCH 9:28 P.M.',
  game:'../college-baseball/game.html?id=cb-2024-02-23-iowa-auburn-att0235',
  paragraphs:[
   'What was originally scheduled to begin at 6:00 p.m. turned into an unforgettable late-night college baseball experience on February 23, 2024. After a delay of nearly three and a half hours, No. 18 Iowa and No. 14 Auburn finally took the field at 9:28 p.m. in Jacksonville, Florida, for their opening matchup of the Jax College Baseball Classic.',
   'The early innings belonged to Iowa and its electric right-handed starter, Brody Brecht. Featuring a fastball that reached triple-digit velocity, Brecht overwhelmed Auburn’s lineup with 11 strikeouts across six innings, allowing just two hits, two runs (one earned), and four walks. His combination of premium velocity and swing-and-miss stuff made the performance one of the Archive’s most memorable pitching showcases.',
   'Iowa carried a 3–2 advantage into the seventh inning, but Auburn capitalized once Brecht departed. Mason Maners tied the game with a solo home run before Bobby Peirce delivered the decisive blow, a two-run homer that put the Tigers ahead 5–3. Christian Hall, who had already driven in a run against Brecht in the sixth, added a solo home run in the eighth as Auburn extended its lead to 7–3.',
   'Hall finished 2-for-4 with a home run and two RBI, while Peirce’s two-run homer proved to be the game’s defining swing. Auburn’s bullpen also delivered, with John Armstrong and Cam Tilly combining for 4⅔ scoreless innings after the starter exited. Iowa threatened one final time with a two-run home run from Sam Petersen in the ninth, but Auburn held on for the 7–5 victory.',
   'Between the unusually late first pitch, Brecht’s triple-digit fastball and 11-strikeout performance, and Auburn’s dramatic late-inning power surge, this game embodied the unpredictability that makes college baseball so memorable. An evening that began with hours of waiting ended with a showcase of elite talent and an exciting comeback under the Jacksonville lights.'
  ],
  columns:['H-AB / IP','HR / H','RBI / ER','BB / K'],
  players:[['Brody Brecht (P)','6.0 IP','2 H','1 ER','4 BB · 11 K'],['Bobby Peirce','1-4','1','2','—'],['Christian Hall','2-4','1','2','—'],['Mason Maners','1-2','1','1','2 BB'],['Sam Petersen','1-4','1','2','—']]
 },
 '2025-05-16':{
  title:'A record Iowa crowd witnesses Oregon’s four-run comeback',
  score:'Oregon 9 · Iowa 6',
  venue:'Duane Banks Field · Iowa City, Iowa · Record attendance: 3,339',
  image:'./oregon-iowa-2025.webp',
  photoAlt:'Oregon baseball players celebrating in front of the Iowa crowd at Duane Banks Field',
  caption:'MAY 16, 2025 · OREGON AT IOWA · JACOB WALSH',
  game:'../college-baseball/game.html?id=cb-2025-05-16-oregon-iowa-att0348',
  paragraphs:[
   'May 16, 2025, was a historic evening for Iowa baseball, as a record crowd of 3,339 fans packed Duane Banks Field to watch the Hawkeyes face No. 5 Oregon in a pivotal late-season Big Ten matchup. The home crowd had plenty to celebrate early, but the Ducks ultimately delivered a memorable comeback in a 9–6 victory.',
   'After Oregon opened the scoring in the first inning, Iowa seized momentum with three runs in the third and another in the fourth. Back-to-back solo home runs by Caleb Wulf and Daniel Rogers in the fifth extended the Hawkeyes’ advantage to 6–2, putting Iowa in command in front of the largest crowd in the ballpark’s history.',
   'Oregon’s offense, however, refused to go quietly. Jacob Walsh was the centerpiece of the comeback, finishing 3-for-5 with two doubles, a home run, two RBI, and three runs scored. His solo home run in the fifth traveled an estimated 445 feet, while Anson Aroz added a 430-foot home run in the sixth to begin closing the gap.',
   'The decisive blow came in the seventh inning. Oregon erupted for four runs, with Walsh delivering an RBI double before Ryan Cooney’s two-run double gave the Ducks their first lead since the opening innings. Oregon added two insurance runs in the ninth, while its bullpen shut out Iowa over the final four innings.',
   'Walsh’s three extra-base hits, Aroz’s home run, and the Ducks’ late offensive surge made this an exceptional game to witness. Combined with Iowa’s historic attendance and the atmosphere surrounding a pivotal conference series, the evening became a memorable chapter in the Courtside Archive.'
  ],
  columns:['H-AB','2B','HR','RBI'],
  players:[['Jacob Walsh','3-5','2','1','2'],['Anson Aroz','2-3','0','1','1'],['Ryan Cooney','2-4','1','0','2'],['Caleb Wulf','2-4','0','1','2'],['Daniel Rogers','2-4','0','1','1']]
 },
 '2025-05-23':{
  title:'Two LSU aces combine for 16 strikeouts as LaViolette plays through injury',
  score:'LSU 4 · Texas A&M 3',
  venue:'Hoover Metropolitan Stadium · Hoover, Alabama · SEC Tournament quarterfinal',
  image:'./lsu-texas-am-2025.webp',
  photoAlt:'LSU left-hander Kade Anderson pitching during the SEC Tournament',
  caption:'MAY 23, 2025 · TEXAS A&M VS. LSU · KADE ANDERSON',
  game:'../college-baseball/game.html?id=cb-2025-05-23-texas-a-m-lsu-att0361',
  paragraphs:[
   'A rare opportunity to witness two of college baseball’s premier pitchers in the same game made LSU’s 4–3 victory over Texas A&M in the 2025 SEC Tournament quarterfinals an unforgettable entry in the Courtside Archive.',
   'LSU turned to its two aces to cover all nine innings. Kade Anderson delivered a dominant six-inning start, striking out 12 Aggies while allowing four hits, one walk, and three earned runs. Anthony Eyanson, normally a member of LSU’s starting rotation, entered in the seventh and finished the game with three scoreless innings, four strikeouts, and his first save of the season. Together, the pair combined for 16 strikeouts across nine innings, showcasing two exceptional arms on the same night.',
   'Yet perhaps the most remarkable individual story belonged to Texas A&M’s Jace LaViolette. Just one day after suffering a broken left hand against Auburn and undergoing surgery that evening, LaViolette returned to the lineup against two of the nation’s most formidable pitchers. He finished 1-for-3 with two RBI, including an RBI single and a sacrifice fly, accounting for two of Texas A&M’s three runs.',
   'Ethan Frey’s two-run home run in the third inning ultimately provided LSU with the winning margin. The Tigers held on for a 4–3 victory, advancing to the SEC Tournament semifinals. For the Archive, the game represents a remarkable convergence of elite pitching talent and competitive determination, made even more memorable by LaViolette’s courageous performance.'
  ],
  columns:['IP / H','ER','BB / K','Decision / Batting'],
  players:[['Kade Anderson','6.0 / 4','3','1 / 12','Win'],['Anthony Eyanson','3.0 / 2','0','1 / 4','Save'],['Jace LaViolette','—','—','—','1-for-3 · 2 RBI'],['Ethan Frey','—','—','—','2-for-3 · 2B · HR · 3 RBI']]
 },
 '2007-03-18':{
  title:'Kobe’s historic streak meets Garnett’s Timberwolves',
  score:'Los Angeles Lakers 109 · Minnesota Timberwolves 102',
  venue:'Staples Center · Los Angeles, California',
  image:'./timberwolves-lakers-2007.webp',
  caption:'MARCH 18, 2007 · KOBE BRYANT AND KEVIN GARNETT',
  game:'../nba/game.html?id=7',
  paragraphs:[
   'March 18, 2007, featured an extraordinary battle between two of the NBA’s defining superstars in their primes, Kobe Bryant and Kevin Garnett, as the Los Angeles Lakers defeated the Minnesota Timberwolves 109–102 at Staples Center.',
   'Bryant delivered a remarkable 50-point performance, shooting 17-for-35 from the field, 4-for-9 from three-point range, and 12-for-14 at the free-throw line. He added six rebounds, three assists, and three steals in the victory. The performance marked the second of four consecutive games in which Bryant scored at least 50 points, placing this night in the middle of one of the most extraordinary scoring stretches in NBA history.',
   'Minnesota countered with outstanding performances of its own. Garnett showcased his exceptional all-around abilities, finishing with 26 points, 15 rebounds, six assists, and three blocks while shooting 9-for-16 from the field. Ricky Davis was equally impressive, leading the Timberwolves with 33 points, six rebounds, and six assists while connecting on four three-pointers.',
   'With three players delivering exceptional statistical performances, two generational talents competing at the height of their careers, and Bryant making history during his legendary scoring streak, this game stands as one of the defining early experiences of the Courtside Archive.'
  ],
  photoAlt:'Kobe Bryant at the rim with Kevin Garnett nearby during the March 18, 2007 Lakers and Timberwolves game',
  columns:['PTS','REB','AST','More'],
  players:[['Kobe Bryant','50','6','3','3 steals · 4 threes'],['Kevin Garnett','26','15','6','3 blocks'],['Ricky Davis','33','6','6','4 threes']]
 },
 '2026-05-16':{
  title:'A ten-run opening, a nine-run comeback, and 28 runs',
  score:'Arkansas 16 · Kentucky 12',
  venue:'Kentucky Proud Park · Lexington, Kentucky',
  image:'./arkansas-kentucky-2026.webp',
  photoAlt:'Arkansas players celebrating during the May 16, 2026 game against Kentucky',
  caption:'MAY 16, 2026 · ARKANSAS AT KENTUCKY',
  game:'../college-baseball/game.html?id=cb-2026-05-16-arkansas-kentucky-att0424',
  paragraphs:[
   'What began with a 40-minute rain delay turned into one of the wildest offensive games in Courtside Archive history, as Arkansas outlasted Kentucky 16–12 in an extraordinary back-and-forth contest at Kentucky Proud Park on May 16, 2026.',
   'The Razorbacks wasted absolutely no time taking control, exploding for 10 runs in the top of the first inning. Kentucky was forced to use three pitchers just to escape the opening frame, and by the top of the fourth, Arkansas had built a seemingly insurmountable 12–2 advantage.',
   'But the Wildcats were far from finished. In an astonishing fifth-inning rally, Kentucky erupted for nine runs in the bottom half, completing an unlikely comeback to tie the game at 12. What had appeared to be a blowout suddenly became a dramatic contest with both teams fighting for control.',
   'Arkansas ultimately regained the advantage, scoring twice in the sixth inning before adding two insurance runs in the ninth to secure the 16–12 victory. Zack Stewart led the Razorbacks’ offensive attack with four hits in six at-bats, including two doubles, a home run, and four RBI. Kentucky’s Jayce Tharnish delivered an impressive performance of his own, going 3-for-6 with a home run and three RBI.',
   'With 28 combined runs, enormous momentum swings, and one of the most improbable rallies witnessed in the Archive, this game stands as an unforgettable example of how quickly a college baseball game can change. From a ten-run opening inning to a stunning comeback and a final Arkansas response, nearly every chapter of this contest delivered something extraordinary.'
  ],
  columns:['H-AB','2B','HR','RBI'],
  players:[['Zack Stewart','4-6','2','1','4'],['Jayce Tharnish','3-6','1','1','3']]
 },
 '2026-04-05':{
  title:'Cade Arrambide hits four home runs in a 12-inning epic',
  score:'LSU 16 · Tennessee 6 · 12 innings',
  venue:'Lindsey Nelson Stadium · Knoxville, Tennessee',
  image:'./lsu-tennessee-2026-arrambide.webp',
  photoAlt:'Cade Arrambide, number 0, celebrating with LSU teammates',
  caption:'APRIL 5, 2026 · LSU AT TENNESSEE · CADE ARRAMBIDE',
  game:'../college-baseball/game.html?id=cb-2026-04-05-lsu-tennessee-att0407',
  paragraphs:[
   'April 5, 2026, produced one of the most extraordinary individual offensive performances in Courtside Archive history, as LSU defeated Tennessee 16–6 in a remarkable 12-inning contest at Lindsey Nelson Stadium in Knoxville.',
   'Tennessee appeared to have the upper hand early, jumping to a 5–0 lead after three innings. LSU gradually battled back, scoring once in the fifth, three times in the seventh, and once in the ninth to force extra innings with the score tied at five.',
   'Both teams exchanged runs in the 11th inning, sending the game into the 12th tied 6–6. What followed was an extraordinary offensive explosion. LSU erupted for 10 runs in the top of the 12th, turning a tightly contested extra-inning battle into a stunning 16–6 victory.',
   'At the center of it all was LSU catcher Cade Arrambide, who delivered one of the greatest single-game hitting performances ever witnessed by the Archive. Arrambide went an incredible 5-for-6 with four home runs, seven RBI, and four runs scored. His extraordinary power display became the defining achievement of an already unforgettable afternoon.',
   'Between the early Tennessee lead, LSU’s relentless comeback, an unprecedented offensive outburst in the 12th inning, and Arrambide’s historic four-home-run performance, this game represents the kind of exceptional sporting experience that the Courtside Archive Museum was created to preserve.'
  ],
  columns:['H-AB','HR','RBI','Runs'],
  players:[['Cade Arrambide','5-6','4','7','4']]
 }
,
 '2018-02-17':{
  "title": "Seven Runs in the Seventh: USD Survives Andrew Vaughn’s Five-Hit Showcase",
  "score": "San Diego 11 · California 8",
  "venue": "Fowler Park · San Diego, California",
  "image": "./cal-usd-2018.webp",
  "photoAlt": "California player number 20 rounding second base beside a San Diego infielder",
  "caption": "FEBRUARY 17, 2018 · CALIFORNIA AT SAN DIEGO · SEVEN-RUN SEVENTH",
  "game": "../college-baseball/game.html?id=cb-2018-02-17-california-san-diego-att0003",
  "paragraphs": [
    "On February 17, 2018, San Diego and California delivered a remarkable early-season contest at Fowler Park. A day after dropping its opener to the Golden Bears, the Toreros found themselves in another fight — this time against an opposing first baseman having a nearly perfect afternoon at the plate.",
    "Cal’s Andrew Vaughn went 5-for-5 with two home runs, five RBI and two runs scored. His first homer, a two-run drive to right-center in the third inning off San Diego starter Chris Murphy, tied the game at 4–4. The matchup gained even more significance in hindsight: Murphy reached the major leagues, while Vaughn was selected third overall by the Chicago White Sox in the 2019 MLB Draft.",
    "Murphy still struck out nine over five innings, but Cal carried a 6–4 lead into the bottom of the seventh. Then the game changed completely. Jay Schuyler drove in two with a double down the right-field line; Shane McGuire and Jeff Houghtby supplied run-scoring singles; and a hit batter, a bases-loaded walk and a fielder’s choice helped San Diego pile up seven runs in the inning.",
    "California scored twice in the eighth, but Justin Friedman closed the door on an 11–8 San Diego victory. Six Toreros finished with two hits apiece, while Gabriel Ponce earned the win in relief. It was USD’s first victory of the season and a dramatic example of how one inning can outweigh even an extraordinary individual performance.",
    "For Courtside Archive, this exhibit preserves both sides of an unforgettable game: Vaughn’s five-hit, two-homer statement against a future big leaguer and the Toreros’ seven-run rally that turned a loss into an exhilarating comeback."
  ],
  "columns": [
    "H-AB",
    "HR",
    "RBI",
    "Context"
  ],
  "players": [
    [
      "Andrew Vaughn",
      "5-5",
      "2",
      "5",
      "2019 MLB Draft · No. 3 overall"
    ],
    [
      "Jay Schuyler",
      "2 hits",
      "—",
      "2",
      "Two-run double sparked seventh"
    ],
    [
      "Chris Murphy",
      "5 IP",
      "—",
      "9 K",
      "Future MLB pitcher"
    ],
    [
      "Gabriel Ponce",
      "2 IP",
      "—",
      "3 K",
      "Winning reliever"
    ]
  ]
}
,
 '2018-09-28':{
  "title": "Fifteen Innings in September: Two Tying Homers and a Galvis Walk-Off",
  "score": "San Diego Padres 3 · Arizona Diamondbacks 2 · 15 innings",
  "venue": "Petco Park · San Diego, California · Late-September expanded rosters",
  "image": "./padres-dbacks-2018.avif",
  "photoAlt": "San Diego Padres players celebrating their September 2018 walk-off victory",
  "caption": "SEPTEMBER 28, 2018 · DIAMONDBACKS AT PADRES · 15-INNING WALK-OFF",
  "game": "../mlb/index.html",
  "paragraphs": [
    "September 28, 2018, was the sort of late-season baseball night that became more interesting the longer it went. Neither Arizona nor San Diego was headed to October, but September’s expanded rosters offered a fascinating mix of established names, developing players and extra bench options. At Petco Park, they needed nearly every bit of that depth during a 15-inning marathon.",
    "The game began as a pitchers’ duel. Rookie Eric Lauer gave San Diego 6⅓ innings without allowing an earned run, while Arizona left-hander Patrick Corbin worked five scoreless frames in what proved to be one of his final starts for the Diamondbacks. Arizona finally broke through in the seventh when Chris Owings scored on a passed ball, but José Pirela answered immediately with a solo home run to tie the game at one.",
    "The score stayed level until the 12th, when Ketel Marte crossed on Nick Ahmed’s sacrifice fly after the Padres intentionally walked stars Paul Goldschmidt and David Peralta to load the bases. Down to their final out against Archie Bradley, San Diego turned to Hunter Renfroe — scratched from the starting lineup because he was ill. Renfroe came off the bench and crushed a pinch-hit, 422-foot homer on Bradley’s first pitch to make it 2–2.",
    "An expanded September bench helped deliver the ending, too. Pinch-hitter Javy Guerra worked a leadoff walk against Matt Andriese in the bottom of the 15th. Freddy Galvis, batting for the seventh time, then ripped a double down the right-field line to bring Guerra home and end the game, 3–2. Eight Padres relievers combined to cover 8⅔ innings, including memorable appearances by Brad Wieck and Kirby Yates.",
    "That is why this game belongs in Courtside Archive: a scoreless opening stretch, two separate tying homers, a pinch-hit rescue with two outs in extra innings, a 15th-inning walk-off and a wonderfully varied late-September cast. The outcome mattered less in the standings than the experience of watching the roster unfold for five extra innings."
  ],
  "columns": [
    "Contribution",
    "Moment",
    "Inning",
    "Context"
  ],
  "players": [
    [
      "Freddy Galvis",
      "Walk-off RBI double",
      "15th",
      "Seventh plate appearance"
    ],
    [
      "Hunter Renfroe",
      "Pinch-hit solo HR",
      "12th",
      "Tied game with two outs"
    ],
    [
      "José Pirela",
      "Solo HR",
      "7th",
      "First Padres equalizer"
    ],
    [
      "Javy Guerra",
      "Pinch-hit walk, winning run",
      "15th",
      "September bench contribution"
    ],
    [
      "Eric Lauer",
      "6⅓ IP · 0 ER · 6 K",
      "Start",
      "Rookie-season finale"
    ],
    [
      "Patrick Corbin",
      "5 scoreless IP",
      "Start",
      "Arizona ace"
    ]
  ]
}
,
 '2018-11-10':{
  "title": "The Air Raid Meets the Ground Game: 1,345 Yards of Football History",
  "score": "San Diego 56 · Davidson 52",
  "venue": "Torero Stadium · San Diego, California · PFL championship clincher",
  "image": "./davidson-usd-2018-photo.webp",
  "photoAlt": "San Diego and Davidson football players during the November 10, 2018 shootout",
  "caption": "NOVEMBER 10, 2018 · DAVIDSON AT SAN DIEGO · RECORD-SETTING SHOOTOUT",
  "game": "../cfb/game.html?id=cfb-2018-11-10-davidson-usd",
  "paragraphs": [
    "November 10, 2018, brought two entirely different offensive philosophies into Torero Stadium — and neither could be stopped. San Diego leaned on the arm of Anthony Lawrence and the extraordinary receiving ability of Michael Bandy. Davidson answered with a rushing attack so explosive that it would set an FCS single-game record. The result was a 56–52 thriller that clinched another Pioneer Football League championship for USD.",
    "Davidson’s rushing trio announced itself with three breathtaking first-quarter touchdown runs: Wesley Dugger raced 94 yards, William Wicks broke free for 90, and Keylan Brown added an 80-yard score. The Wildcats amassed 789 rushing yards, paced by Dugger’s 231, Wicks’s 197 and Brown’s 150; quarterback Tyler Phelps contributed another 153. Four Wildcats exceeded 150 yards on the ground, and Davidson twice built a 24-point first-half lead.",
    "San Diego had the perfect counterpunch. Lawrence completed 24 passes for a school-record 556 yards and seven touchdowns, while Bandy caught 10 passes for 324 yards and four scores. Dalton Kincaid added two touchdown catches, and the Toreros cut a 38–14 second-quarter deficit to just 38–35 at halftime. The game was a showcase of overwhelming ground production on one side and devastating downfield precision on the other.",
    "The defining sequence came late. After a fourth-down stop at the San Diego one-yard line, Lawrence found Bandy for a stunning 99-yard touchdown that gave USD a 49–45 fourth-quarter lead. Davidson responded, and Brown’s 12-yard scoring run put the Wildcats ahead 52–49 with 2:38 remaining. Lawrence answered in just 55 seconds, finding Bandy for 46 yards before connecting with him for the winning 20-yard touchdown with 1:43 left.",
    "USD survived 56–52 and secured the PFL title and FCS playoff berth, even as Davidson departed with a national rushing record. For Courtside Archive, the numbers almost defy belief: 556 passing yards from Lawrence, 324 receiving yards from Bandy, 789 rushing yards for Davidson, and a championship decided by one final Lawrence-to-Bandy connection. A game that truly speaks for itself."
  ],
  "columns": [
    "Signature",
    "Yards",
    "TD",
    "Context"
  ],
  "players": [
    [
      "Anthony Lawrence",
      "Passing",
      "556",
      "7",
      "USD single-game passing record"
    ],
    [
      "Michael Bandy",
      "Receiving",
      "324",
      "4",
      "10 catches · 99-yard TD"
    ],
    [
      "Wesley Dugger",
      "Rushing",
      "231",
      "1",
      "94-yard touchdown run"
    ],
    [
      "William Wicks",
      "Rushing",
      "197",
      "3",
      "90-yard touchdown run"
    ],
    [
      "Tyler Phelps",
      "Rushing",
      "153",
      "1",
      "Davidson quarterback"
    ],
    [
      "Keylan Brown",
      "Rushing",
      "150",
      "2",
      "80-yard touchdown run"
    ]
  ]
}
};
const root=document.getElementById('greatestGamesList'),sportEl=document.getElementById('greatestGamesSport'),sortEl=document.getElementById('greatestGamesSort'),searchEl=document.getElementById('greatestGamesSearch'),countEl=document.getElementById('greatestGamesCount');
if(!root)return;
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const formatDate=date=>new Date(date+'T12:00:00Z').toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric',timeZone:'UTC'});
const candidatePhotos={'2018-09-28':'./padres-dbacks-2018.avif','2018-02-17':'./cal-usd-2018.webp','2018-11-10':'./davidson-usd-2018-photo.webp','2019-02-20':'./nevada-sdsu-2019-photo.webp','2019-02-22':'./oklahoma-usd-2019.webp','2019-11-30':'./emu-uci-2019.webp','2020-02-28':'./monmouth-usd-2020.webp','2022-03-05':'./dbu-usd-2022.webp','2022-05-28':'./usd-gonzaga-wcc-2022.webp'};
const candidatePhotoDetails={'2018-09-28':{alt:'San Diego Padres players celebrating their September 2018 walk-off victory',caption:'SEPTEMBER 28, 2018 · D-BACKS AT PADRES · POSTGAME CELEBRATION'},'2018-02-17':{alt:'California player number 20 rounding second base beside a San Diego infielder',caption:'FEBRUARY 17, 2018 · CALIFORNIA AT SAN DIEGO'},'2019-02-22':{alt:'Oklahoma batter number 5 swinging during the game against San Diego',caption:'FEBRUARY 22, 2019 · OKLAHOMA AT SAN DIEGO'},'2019-11-30':{alt:'UC Irvine number 40 taking a jump shot against Eastern Michigan',caption:'NOVEMBER 30, 2019 · EASTERN MICHIGAN AT UC IRVINE'},'2020-02-28':{alt:'San Diego pitcher number 32 delivering a pitch against Monmouth',caption:'FEBRUARY 28, 2020 · MONMOUTH AT SAN DIEGO'},'2022-03-05':{alt:'San Diego pitcher number 35 delivering a pitch against Dallas Baptist',caption:'MARCH 5, 2022 · DALLAS BAPTIST AT SAN DIEGO'},'2022-05-28':{alt:'San Diego players celebrating the 2022 West Coast Conference baseball championship with the trophy',caption:'MAY 28, 2022 · SAN DIEGO VS. GONZAGA · WCC CHAMPIONS'} };
const expanded=new Set();
const label=g=>g.site==='neutral'?`${g.away} vs. ${g.home}`:`${g.away} @ ${g.home}`;
function content(g){const s=stories[g.date];if(!s)return `<div class="gg-pending">${candidatePhotos[g.date]?`<figure class="gg-photo"><img src="${esc(candidatePhotos[g.date])}" alt="${esc(candidatePhotoDetails[g.date]?.alt||'Game photo')}" loading="lazy"><figcaption>${esc(candidatePhotoDetails[g.date]?.caption||'GAME PHOTO')}</figcaption></figure>`:''}<p>This game has been nominated for the permanent collection. The photograph is uploaded; the full story, selected performances and box-score link await review.</p></div>`;
 return `<div class="gg-story-layout"><figure class="gg-photo">${s.image?`<img src="${esc(s.image)}" alt="${esc(s.photoAlt)}" loading="lazy">`:`<span class="gg-sport-symbol" aria-label="Photo awaiting upload">⚾</span>`}<figcaption>${esc(s.caption)}</figcaption></figure><div class="gg-narrative"><span class="eyebrow">THE GAME STORY</span><h3>${esc(s.title)}</h3><p class="gg-final">${esc(s.score)}</p><p class="gg-venue">${esc(s.venue)}</p>${s.paragraphs.map(p=>`<p>${esc(p)}</p>`).join('')}</div></div><div class="gg-performances"><h4>Featured performances</h4><div class="gg-table-wrap"><table><thead><tr><th>Player</th>${s.columns.map(v=>`<th>${esc(v)}</th>`).join('')}</tr></thead><tbody>${s.players.map(p=>`<tr><th scope="row">${esc(p[0])}</th>${p.slice(1).map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div><a class="gg-box-link" href="${esc(s.game)}">View Courtside Archive box score ↗</a></div>`;
}
function render(){root.querySelectorAll('details[open]').forEach(d=>expanded.add(d.dataset.date));
 const sport=sportEl.value,order=sortEl.value,q=searchEl.value.toLowerCase().trim();const matches=candidates.filter(g=>(sport==='all'||g.sport===sport)&&`${g.away} ${g.home} ${g.sport} ${g.date}`.toLowerCase().includes(q)).sort((a,b)=>order==='oldest'?a.date.localeCompare(b.date):b.date.localeCompare(a.date));
 const completed=Object.keys(stories).length;countEl.textContent=`${matches.length} of ${candidates.length} games · ${completed} completed ${completed===1?'story':'stories'}`;
 root.innerHTML=matches.length?matches.map(g=>{const s=stories[g.date],icon=g.sport==='NBA'||g.sport==='College Basketball'?'🏀':g.sport==='NFL'||g.sport==='College Football'?'🏈':'⚾';return `<details class="gg-game ${s?'gg-complete':''}" data-date="${g.date}" ${expanded.has(g.date)?'open':''}><summary><span class="gg-card-image">${(s?.image||candidatePhotos[g.date])?`<img src="${esc(s?.image||candidatePhotos[g.date])}" alt="" loading="lazy">`:`<span class="gg-sport-symbol" aria-hidden="true">${icon}</span>`}<span class="gg-card-year">${g.date.slice(0,4)}</span></span><span class="gg-card-body"><span class="gg-card-sport">${esc(g.sport)}</span><strong>${esc(label(g))}</strong><span class="gg-date">${formatDate(g.date)}</span><small>${s?esc(s.score):'Story pending'}</small><span class="gg-card-action">${s?'Explore game story':'View nomination'} <span aria-hidden="true">↗</span></span></span></summary><div class="gg-content">${content(g)}</div></details>`}).join(''):'<p class="gg-empty">No nominated games match these filters.</p>';
 root.querySelectorAll('details').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)expanded.add(d.dataset.date);else expanded.delete(d.dataset.date)}));
}
[sportEl,sortEl,searchEl].forEach(el=>el.addEventListener(el===searchEl?'input':'change',render));render();
})();
