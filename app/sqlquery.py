import pypyodbc
import pandas as pd
import json


cnxn = pypyodbc.connect("Driver={SQL Server Native Client 11.0};"
                    "Server=PRDAEMOSQL02;"
                    "Database=AEMO_MMS;"
                    "Trusted_Connection=yes;")

sql_query = '''
declare @StartingDate smalldatetime
declare @EndingDate smalldatetime
declare @DaysForward int
declare @DaysTotal int
declare @RowsRequired int
declare @SemiSchColumn nvarchar(max)
declare @TimeNow time
declare @FullDateTimeNow smalldatetime

if(datepart(hour, getdate())<4) 
 set @DaysForward =0;
else 
 set @DaysForward =1;

set @SemiSchColumn = 'LOR' --'LOR'--'not LOR' -- Toggle to select either [LOR_SEMISCHEDULEDCAPACITY] or [SEMISCHEDULEDCAPACITY] column
set @DaysTotal = 7 --  Parameter to select number of days to display

set @TimeNow = cast(getdate() as time)
if (DATEPART(minute,getdate())<30)
 set @FullDateTimeNow = dateadd(minute,30,DATEADD(hour,datepart(hour,getdate()), DATEDIFF(dd, 0, GETDATE())));
else
 set @FullDateTimeNow = dateadd(minute,60,DATEADD(hour,datepart(hour,getdate()), DATEDIFF(dd, 0, GETDATE())));

set @StartingDate = dateadd(day,@DaysForward,dateadd(minute,30, dateadd(hour,4,DATEADD(dd, 0, DATEDIFF(dd, 0, GETDATE())))))
set @EndingDate = dateadd(minute,-30,DATEADD(day, @DaysTotal, @StartingDate))

set @RowsRequired = 1 + DATEDIFF(minute,@StartingDate,@EndingDate)/30

--print 'starting date is ' 
--print  @startingdate

--print 'ending date is ' 
--print  @EndingDate

--print 'number of rows is ' 
--print  @RowsRequired

--print 'other method of rows required calcs is '
--print DATEDIFF(dd,@StartingDate,@EndingDate)*48


 SELECT
 lb1.INTERVAL_DATETIME,
 SAMarket.[SA DEMAND],
 SAMarket.[NON-SCHED],
 SAMarket.[SEMI-SCHED],
 LB1_PowerMean,
 LB2_PowerMean,
 LB3_PowerMean,
 LB1_PowerMean+LB2_PowerMean+LB3_PowerMean AS 'Lake Bonney [1,2 & 3]',
 SAPV.POWERMEAN as SolarPV,
 Wind_Cap = 1295
  
  from (select TOP (@RowsRequired)
  [RUN_DATETIME]
      ,[INTERVAL_DATETIME]
      ,[POWERMEAN] as LB1_PowerMean
  FROM [AEMO_MMS].[dbo].[INTERMITTENT_GEN_FCST_DATA]
  where INTERVAL_DATETIME between @StartingDate and @EndingDate
  AND duid ='LKBONNY1'
  and RUN_DATETIME in (select max(run_datetime) from [AEMO_MMS].[dbo].[INTERMITTENT_GEN_FCST_DATA] where INTERVAL_DATETIME between @StartingDate and @EndingDate and RUN_DATETIME >= DATEADD(day,-2,@StartingDate) group by INTERVAL_DATETIME)
  ORDER BY RUN_DATETIME DESC, INTERVAL_DATETIME)  as LB1

JOIN 

  (SELECT TOP (@RowsRequired)
  [RUN_DATETIME]
      ,[INTERVAL_DATETIME]
      ,[POWERMEAN] as LB2_PowerMean
  FROM [AEMO_MMS].[dbo].[INTERMITTENT_GEN_FCST_DATA]
  where INTERVAL_DATETIME between @StartingDate and @EndingDate
  AND duid ='LKBONNY2'
  and RUN_DATETIME in (select max(run_datetime) from [AEMO_MMS].[dbo].[INTERMITTENT_GEN_FCST_DATA] where INTERVAL_DATETIME between @StartingDate and @EndingDate and RUN_DATETIME >= DATEADD(day,-2,@StartingDate) group by INTERVAL_DATETIME)
  ORDER BY RUN_DATETIME DESC, INTERVAL_DATETIME) as LB2
  on lb1.INTERVAL_DATETIME = lb2.INTERVAL_DATETIME

JOIN

  (SELECT TOP (@RowsRequired)
  [RUN_DATETIME]
      ,[INTERVAL_DATETIME]
      ,[POWERMEAN] as LB3_PowerMean
  FROM [AEMO_MMS].[dbo].[INTERMITTENT_GEN_FCST_DATA]
  where INTERVAL_DATETIME between @StartingDate and @EndingDate
  AND duid ='LKBONNY3'
  and RUN_DATETIME in (select max(run_datetime) from [AEMO_MMS].[dbo].[INTERMITTENT_GEN_FCST_DATA] where INTERVAL_DATETIME between @StartingDate and @EndingDate and RUN_DATETIME >= DATEADD(day,-2,@StartingDate) group by INTERVAL_DATETIME)
  ORDER BY RUN_DATETIME DESC, INTERVAL_DATETIME ASC) as LB3
  on lb3.INTERVAL_DATETIME = lb2.INTERVAL_DATETIME

JOIN 

 (SELECT TOP (@RowsRequired)
  [RUN_DATETIME],
  [INTERVAL_DATETIME],
  [DEMAND50] as 'SA DEMAND',
  case @SemiSchColumn
   when 'LOR' then  [LOR_SEMISCHEDULEDCAPACITY]
   when 'not LOR' then [SEMISCHEDULEDCAPACITY]
   else null
  end as 'SEMI-SCHED',
  [TOTALINTERMITTENTGENERATION] as 'NON-SCHED'
  FROM [AEMO_MMS].[dbo].[STPASA_REGIONSOLUTION]
  where REGIONID = 'SA1' 
  AND RUNTYPE = 'OUTAGE_LRC'
  AND INTERVAL_DATETIME between @StartingDate and @EndingDate
  and RUN_DATETIME in (select max(run_datetime) from [AEMO_MMS].dbo.STPASA_REGIONSOLUTION where INTERVAL_DATETIME between @StartingDate and @EndingDate and RUN_DATETIME >= DATEADD(day,-2,@StartingDate) group by INTERVAL_DATETIME)
  ORDER BY RUN_DATETIME desc, INTERVAL_DATETIME ASC) AS SAMarket
  on SAMarket.INTERVAL_DATETIME = lb3.INTERVAL_DATETIME 

JOIN 
 
 (SELECT top (@RowsRequired)
  [VERSION_DATETIME]
      ,[REGIONID]
      ,[INTERVAL_DATETIME]
      ,[POWERMEAN]
  FROM [AEMO_MMS].[dbo].[ROOFTOP_PV_FORECAST]
  where REGIONID = 'SA1'
  and INTERVAL_DATETIME between @StartingDate and @EndingDate
  and [VERSION_DATETIME] in (select max([VERSION_DATETIME]) from [AEMO_MMS].[dbo].[ROOFTOP_PV_FORECAST] where INTERVAL_DATETIME between @StartingDate and @EndingDate and [VERSION_DATETIME] >= DATEADD(day,-2,@StartingDate) group by INTERVAL_DATETIME)

  order by VERSION_DATETIME desc, INTERVAL_DATETIME asc) as SAPV
  on SAPV.INTERVAL_DATETIME = SAMarket.INTERVAL_DATETIME

  ORDER BY SAPV.VERSION_DATETIME desc, lb1.RUN_DATETIME DESC, lb1.INTERVAL_DATETIME
'''

df = pd.read_sql_query(sql_query, cnxn)
timestamps = df['interval_datetime'].tolist()
timestamps = [x.strftime('%Y-%m-%d %H:%M') for x in timestamps]
datestamps = [x.strftime('%a %d-%b') for x in df['interval_datetime'].tolist()]
demand = df['sa demand'].tolist()
datavals =  [{"date": timestamp, "value": demand} for timestamp, demand in zip(timestamps, demand)]
datavals = json.dumps(datavals)

