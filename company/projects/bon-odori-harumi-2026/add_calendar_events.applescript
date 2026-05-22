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
		make new event at end of targetCal with properties {summary:title, start date:s, end date:e}
	end tell
end addEvent

tell application "Calendar"
	set targetCal to calendar calName
end tell

addEvent(targetCal, "【盆踊り】スタッフ募集LINEを流す", 2026, 5, 22, 9, 0, 30)
addEvent(targetCal, "【盆踊り】週次レビュー", 2026, 5, 24, 9, 0, 30)
addEvent(targetCal, "【盆踊り】レイアウト確認・スタッフ一次集計", 2026, 5, 31, 10, 0, 60)
addEvent(targetCal, "【盆踊り】車両使用アンケート対応", 2026, 6, 5, 10, 0, 30)
addEvent(targetCal, "【盆踊り】運営設計デッドライン", 2026, 6, 7, 10, 0, 60)
addEvent(targetCal, "【盆踊り】販売価格・目標数量決定", 2026, 6, 15, 10, 0, 60)
addEvent(targetCal, "【盆踊り】仕入れ・試作・衛生手順確認", 2026, 6, 21, 10, 0, 90)
addEvent(targetCal, "【盆踊り】シフト確定・マニュアル配布", 2026, 6, 30, 10, 0, 60)
addEvent(targetCal, "【盆踊り】本番 Day1（7/11）", 2026, 7, 11, 12, 0, 600)
addEvent(targetCal, "【盆踊り】本番 Day2（7/12）", 2026, 7, 12, 12, 0, 600)
addEvent(targetCal, "【盆踊り】事後精算・振り返り", 2026, 7, 13, 10, 0, 60)

return "created"
