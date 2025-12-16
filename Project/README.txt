hi pookies
--Before you start testing--
Change some stuff in turret_code
Line 40 (the second ip address string) -> ip of whatever computer is hosting the json
Then find your position in the json (just open it in browser and look)
Convert the angle to degrees and position the turret as per usual
Line 35 (offset) second number -> our degrees position (this is so we can reference to the center post)
--Zero the laser--
Aim the laser at the center pole/point/whatever. Height is unimportant, just make sure it hits it as centered as possible
Use arrows or vert input to get laser firing into the little hole (If using the input boxes, make sure to keep the horizontal angle the same, it needs two inputs)
Zero at the little hole
Send the vertical to 90 and zero again
This should now be pointing at the center pole, with the laser perfectly horizontal. 
--Testing--
Use the arrows or input boxes to aim the laser at something
Input its coordinates into the Reference boxes (degrees and mm)
Hit reference
Repeat. After three references, it will automatically calibrate its position and display it. If it looks fucked, take out whatever point from the lsit you think is bad and add another. 
If its really fucked, let me know :(((
You can also just set line 30 -> JSON position and just not calibrate. It should be close enough. Make sure the second value is radians though
--Pew Pew--
Test prints all the JSON positions
Destroy aims at each one and fires
Yeah