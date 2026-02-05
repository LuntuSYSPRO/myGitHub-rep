/* Insert this into Sysprodb */

INSERT INTO [dbo].[AdmTileDefinition]
           ([TileName]
           ,[TileId]
           ,[Description]
           ,[HelpText]
           ,[TileType]
           ,[TileCategory]
           ,[TileActivityList]
           ,[TileKeyType]
           ,[CustomFlag]
           ,[TileInDevelopment]
           ,[DetailAvailable]
           ,[DetailShowCols]
           ,[ParamInfo1]
           ,[ParamInfo2]
           ,[ParamInfo3]
           ,[ParamInfo4]
           ,[ParamInfo5]
           ,[ParamInfo6]
           ,[ParamInfo7]
           ,[ParamInfo8]
           ,[ParamInfo9]
           ,[ParamInfo10]
           ,[TileDefinition]
           ,[CreatedDate]
           ,[CreatedBy]
           ,[UpdatedDate]
           ,[UpdatedBy])
     VALUES
           ('USR004_SQL',
		   'USR004',
		   'SQL',
		   '',
		   'Text',
		   'AADuppie',
		   '',
		   'C',
		   'N',
		   'Y',
		   0,
		   0,
		   'SearchStr;TEST;KeySingle;;;',
		   '',
		   '',
		   '',
		   '',
		   '',
		   '',
		   '',
		   '',
		   '',
		   '-- SYSPRO Tile Definition
-- @(#) Version : 8.0.000     Last updated : 2025/11/06 08:11
-- Last updated by DEMO                      DEMO

--:[Header]
--:TileId          :USR004
--:Description     :SQL
--:Help            :
--:Type            :Text
--:Category        :AADuppie
--:Activity        :
--:KeyType         :

--:[SummaryTile]
--:Title           :SQL
--:SubTitle        :
--:Value           :{Value}
--:Footer          :

--:[Parameters]
--:ParamName       :SearchStr
--:ParamDescription:TEST
--:ParamType       :KeySingle
--:ParamList       :
--:ParamKeyType    :

--:[Preview]
--:PrevSubTitle    :
--:PrevValue       :100
--:PrevFooter      :
--:PrevForeground  :White
--:PrevBackground  :Primary

--:[SummarySQL]
-- SYSPRO Tile Definition
    DECLARE @searchStr VARCHAR(20)',
	'2025-11-06 07:56:08.680',
	'ADMIN',
	'2025-11-06 08:11:23.070',
	'ADMIN')
GO


