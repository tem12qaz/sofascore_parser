from pprint import pprint

dic = {"tournament":{"name":"LaLiga","slug":"laliga","category":{"name":"Spain","slug":"spain","sport":{"name":"Football","slug":"football","id":1},"id":32,"flag":"spain","alpha2":"ES"},"uniqueTournament":{"name":"LaLiga","slug":"laliga","category":{"name":"Spain","slug":"spain","sport":{"name":"Football","slug":"football","id":1},"id":32,"flag":"spain","alpha2":"ES"},"userCount":0,"id":8,"hasEventPlayerStatistics":'true',"hasPerformanceGraphFeature":'false',"displayInverseHomeAwayTeams":'false'},"priority":335,"id":36},"roundInfo":{"round":16},"customId":"vgbsAgb","status":{"code":100,"description":"Ended","type":"finished"},"winnerCode":3,"homeTeam":{"name":"Athletic Club","slug":"athletic-club","shortName":"Athletic","sport":{"name":"Football","slug":"football","id":1},"userCount":0,"disabled":'false',"type":0,"id":2825,"subTeams":[],"teamColors":{"primary":"#52b030","secondary":"#52b030","text":"#ffffff"}},"awayTeam":{"name":"Osasuna","slug":"osasuna","shortName":"Osasuna","sport":{"name":"Football","slug":"football","id":1},"userCount":0,"type":0,"id":2820,"subTeams":[],"teamColors":{"primary":"#52b030","secondary":"#52b030","text":"#ffffff"}},"homeScore":{"current":0,"display":0,"period1":0,"period2":0,"normaltime":0},"awayScore":{"current":0,"display":0,"period1":0,"period2":0,"normaltime":0},"time":{"injuryTime1":1,"injuryTime2":4,"currentPeriodStartTimestamp":1673301089},"changes":{"changes":["status.code","status.description","status.type","homeScore.period2","homeScore.normaltime","awayScore.period2","awayScore.normaltime","time.currentPeriodStart"],"changeTimestamp":1673301091},"hasGlobalHighlights":'true',"hasEventPlayerStatistics":'true',"hasEventPlayerHeatMap":'true',"detailId":1,"id":10408320,"startTimestamp":1673294400,"slug":"athletic-club-osasuna","finalResultOnly":'false'}
pprint(dic)