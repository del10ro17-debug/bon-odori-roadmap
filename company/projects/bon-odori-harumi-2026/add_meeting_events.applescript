property calName : "仕事"

on makeStart(y, m, d, h, min)
	set t to current date
	set year of t to y
	set month of t to m
	set day of t to d
	set hours of t to h
	set minutes of t to min
	set seconds of t to 0
	return t
end makeStart

on addEvent(targetCal, title, y, m, d, h, min, durationMinutes)
	set s to makeStart(y, m, d, h, min)
	set e to s + (durationMinutes * minutes)
	tell application "Calendar"
		if title contains "坂倉家" then
			make new event at end of targetCal with properties {summary:title, start date:s, end date:e, location:"坂倉家"}
		else
			make new event at end of targetCal with properties {summary:title, start date:s, end date:e}
		end if
	end tell
end addEvent

tell application "Calendar"
	set targetCal to calendar calName
end tell

addEvent(targetCal, "【盆踊り】認識合わせMTG（坂倉家）", 2026, 5, 30, 19, 30, 60)
addEvent(targetCal, "【盆踊り】準備完結MTG（中澤家出国前）", 2026, 6, 13, 19, 0, 90)

return "created"
