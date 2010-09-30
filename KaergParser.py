### Name      : Kaerg Parser.
### Solution  : Refactorisation of __init__ and Object Aggregation in Finite Semantic
### Descendant/Parser with executive clauses...
###

import  sys, os, re, urllib, urllib2, cStringIO, uuid, pynav, passogva, random
from    pynav   import Pynav
import  lxml
from    uuid    import uuid4

from formbuild      import Form
from lxml           import html
from lxml.cssselect import CSSSelector
from lxml.html      import fromstring, tostring
from lxml.html      import parse, submit_form
from lxml.html      import clean
##from clean          import clean_html


def RandomParamMaker( defaultMinArg=3   , defaultMaxArg=6                 ,  MaxLengthDict=5       ,
                      MinDistancePair=3 , DefaultDecreaseMaxArgFactor=100 ,  DefaultMaxFactorReg=5 , MaxArgFactorInfl=10 ):
  ParamDict=dict()
  CountInnerLoop=0
  CountPerInflation=0
  if defaultMaxArg-defaultMinArg < MinDistancePair:
    defaultMaxArg=defaultMaxArg+ MinDistancePair
  SaveMaxArg=defaultMaxArg
  SaveMinArg=defaultMinArg
  while len( ParamDict.keys() ) <= MaxLengthDict:
    TupleParam=passogva.generate_password( minlen=defaultMinArg, maxlen=defaultMaxArg )
    ListParam=TupleParam[1].split('-')
    for Item in ListParam:
      if len( Item ) >= defaultMinArg:
        StreamVariableReduc=str( uuid4() ).replace( '-', '' ) * 5
        StartCopyPart=0
        EndCopyPart=random.randint( 1, len( StreamVariableReduc )-1 )
        ParamDict[Item]=StreamVariableReduc[StartCopyPart:EndCopyPart]
    if CountInnerLoop >= DefaultDecreaseMaxArgFactor:
      print "Present Pair Value <<%d, %d >> exceed DecreaseMaxArgFactor : %d \n\tCurrent DictKey:[ %s ]" % ( defaultMinArg , defaultMaxArg, DefaultDecreaseMaxArgFactor, ParamDict.keys() )
      if defaultMinArg >= defaultMaxArg:
        SaveMinArg+=1
        SaveMaxArg+=1
        defaultMinArg=SaveMinArg
        defaultMaxArg=SaveMaxArg
      defaultMinArg+=1
      CountInnerLoop=0
      CountPerInflation+=1
      if CountPerInflation == DefaultMaxFactorReg:
        DefaultDecreaseMaxArgFactor+=MaxArgFactorInfl
        if ( ( defaultMinArg-(MaxArgFactorInfl / 2) ) > 0 ) and ( ( defaultMinArg-( MaxArgFactorInfl / 2 ) < defaultMaxArg ) ):
          defaultMinArg=( defaultMinArg - ( MaxArgFactorInfl / 2 ) )
        CountPerInflation=0
    CountInnerLoop+=1
  print "Returned Dict:[ %s ]" % ( ParamDict.keys() )
  return ParamDict

def GetListRandSorted( minRange=3, maxRange=32, lengthRange=3 ):
  valDict=[]
  ValRangeOut=lengthRange-1
  ValRangeCount=0
  while ValRangeCount <= ValRangeOut:
    valueRand=random.randint( minRange, maxRange )
    if not valueRand in valDict:
      valDict.append( valueRand )
      ValRangeCount+=1
  valDict.sort()
  print "Returned List[ %s ]" % ( valDict )
  return valDict

class ObjectReturn( object ):
  OriginAttrName=None
  DestAttrName=None
  ContentTransfertAttr=None
  
  def update( self , **Kargs ):
    for ItemNameKey in Kargs.keys():
      ItemNameValue = Kargs[ItemNameKey]
      if not hasattr( self, ItemNameKey  ):
        self.__setattr__( ItemNameKey, ItemNameValue )

  def GetTransfert( self ):
    TupleDisplay=( self.OriginAttrName , self.DestAttrName, self.ContentTransfertAttr )
    return TupleDisplay

  def SetTransfert( self, value ):
    self.OriginAttrName , self.DestAttrName, self.ContentTransfertAttr = value
    setattr( self, self.DestAttrName, getattr( self, self.OriginAttrName )( self.ContentTransfertAttr ) )

  def __init__( self , **Kargs ):
    self.update( **Kargs )

def GetLinkFromRegExpSpec( RegExpList, ListLink, DictValueSendOnPageRequest ):
  UrlQuery=None
  LinkMatchRegExp=dict()
  for IntItemRegTest in range( 0 , len( RegExpList ) ):
    for IntItemLink in range( 0 , len( ListLink ) ):
      if RegExpList[IntItemRegTest].search( ListLink[IntItemLink] ) != None:
        if PrintLinkRegExrSearch:
          print "\n\tMatch Expression %d with item : %s " % ( IntItemRegTest, ListLink[IntItemLink] )
        if not IntItemLink in LinkMatchRegExp.keys():
          LinkMatchRegExp[IntItemLink]=dict()
        LinkMatchRegExp[IntItemLink][IntItemRegTest]=True

  for itemKey in LinkMatchRegExp.keys():
    if len( LinkMatchRegExp[itemKey].keys() ) == len( RegExpList ):
      print "Loging Preference : %s " % ( ListLink[itemKey] )
      UrlQuery=ListLink[itemKey]
  return UrlQuery


class Kaerg():
  @staticmethod
  def __AddMainDict__( ClassName, Item, ArgDict ):
    print "from classname < %s <%s; %s>> " % ( ClassName.__name__ , Item , ArgDict[Item] )
    __builtins__.setattr( ClassName , Item,  ArgDict[Item] )
    
  @classmethod
  def Parser( cls, ClassName, BindValue=False, **Kargs ):
    if BindValue:
      [ cls.__AddMainDict__( ClassName ,ItemVarValue, Kargs ) for ItemVarValue in Kargs ]

class NNDBConf():
  Post={  1:{ 'name':('query'),
              'value':('paris hilton'),
              'form_id':(0)} }
         
  def __init__( self, BindValue=False, **Kargs ):
    Kaerg.Parser( self.__class__ , BindValue, **Kargs )
  
class JobboomConf():
  Post={  1:{ 'name':('username'),
              'value':(''),
              'form_id':(1) },
          2:{ 'name':('password'),
              'value':(''),
              'form_id':(1)} }
         
  def __init__( self, BindValue=False, **Kargs ):
    Kaerg.Parser( self.__class__ , BindValue, **Kargs )

class AldderIdes():

  class Aldder( Exception ):
    class NoLXMLModule( Exception ):
      DefaultMsg="No Lxml Module loaded"

      def __init__( self, msg):
        Exception.__init__( self, msg )
    class StdNoLXMLModule( NoLXMLModule ):
      def __init__( self ):
        Exception.__init__( self, self.NoLXMLModule.DefaultMsg )
  class Ides( Warning ):
    class NoUrlVariableFound( Warning ):
      def __init__(self, msg):
        Warning.__init__( self, msg )

    class EmptyUrlVariableFound( Warning ):
      def __init__(self, msg):
        Warning.__init__( self, msg )

    class ConfClass( Warning ):
      def __init__(self, msg):
        Warning.__init__( self, msg )

    class ConfPostDictNotAvailable( Warning ):
      def __init__(self, msg):
        Warning.__init__( self, msg )

  FileNameHtmlTransit='/home/ubuntu/test-file.html'

  """ Don't forget,
      The ListProc, can be overwritten while Instanciating new object/instance, leaving the
      process to interrupt at a specific moment. Ex:
      ListProc=[ '__MainRegistryAttr__', 'QueryUrl' ,'LxmlModuleFromString' , 'CheckModuleFormPost',
             'ParseForm'  ]
      - This case will stop at the ParseForm, before sending information, It's good inspecting... Some
      Action can be relative and may not hold website... Use the JobboomConf Example with the previous version
      to see the problems, The actual 'Enhancing' arbritrary use a try-except inside the SendForm to
      re-craft the action...

      Hold your Breath... Old story of 2004, a Dude guy beleiving in the Cross-script scripting thru a
      anomalies tested here @VDL2 session during 2003/2004... Why a guy want  explicitly your computer
      access, when you decide to remove-it after seeing nobody asking to get a Linux-Shell for testing
      purposes... 
      
  """
  ListProc=[ '__MainRegistryAttr__', 'QueryUrl' ,'LxmlModuleFromString' , 'CheckModuleFormPost',
             'ParseForm' ,'SendForm' ,'__TransitHtmlFile__'  ]
  ListProcName=[ 'ListProc' ]
  UrlNameAttr='Url'  
  ScanHtmlValueWith='name'

  TransfertHtmlValueWith='value'
  FormPostName='Post'
  ConfigurationFormName='QueryConf'
  QueryOrderName='QueryOrderConf'
  WebBufferFormKeyName='form'

  DefaultBufferStore='buffer'
  FormLocatorName='form_id'

  __all__=[ '__RegisterDef__' ]

  def __RegisterDef__( self ):
    if not self.FuncName in self.__all__:
      self.__all__.append( self.FuncName )

  def __MainRegistryAttr__( self ):
    self.FuncName=self.__MainRegistryAttr__.__name__
    self.__RegisterDef__()
    ### Equivalent to self.QueryConf

    self.ObjectQuery=getattr( self, self.ConfigurationFormName )
    ### Equivalent to self.QueryConf.Post
    self.ObjectQueryDict=getattr( self.ObjectQuery , self.FormPostName )
    ### Equivalent to self.QueryConf.Post.keys()
    self.ObjectQueryName=getattr( self.ObjectQuery , '__class__' ).__name__
    ### Equivalent to self.QueryConf.Post.keys()

    self.ObjectQueryDictKeys=getattr( self.ObjectQueryDict, 'keys' )()
    self.WebBuffer[self.WebBufferFormKeyName]=dict()
    self.WebBuffer[self.WebBufferFormKeyName]['query']=list()

  def __ListProcess__(self):
    self.FuncName=self.__ListProcess__.__name__
    self.__RegisterDef__()
    for ItemProcExec in self.ListProcName:
      for ItemListed in getattr( self, ItemProcExec ):
        print "Executing Definition %s" % ( ItemListed )
        getattr( self, ItemListed )()
    
  def __init__( self, BindValue=False, **Kargs ):
    self.FuncName=self.__init__.__name__
    self.__RegisterDef__()
    Kaerg.Parser( self.__class__ , BindValue, **Kargs )
    self.__ListProcess__()

  def TestModuleName( self ):
    MainModuleTest=getattr( self.TestModuleNameAttrLeft, self.TestModuleNameAttrRight )
    ChildModuleTest=getattr( MainModuleTest , self.TesTModuleCompareAttr)( self.TestModuleNameModule )
    return ChildModuleTest

  def LxmlModuleFromString( self ):
    self.FuncName=self.LxmlModuleFromString.__name__
    self.__RegisterDef__()
    if hasattr( self.WebBuffer, '__name__' ):
      self.TestModuleNameAttrLeft=self.WebBuffer
      self.TestModuleNameAttrRight='__name__'
      self.TesTModuleCompareAttr='__eq__'
      self.TestModuleNameModule='lxml'
      if not self.TestModuleName():
        raise self.Aldder.StdNoLXMLModule
    self.WebBuffer['lxml']=fromstring( self.WebBuffer[ self.DefaultBufferStore ] )

  def CheckModuleFormPost( self ):
    self.FuncName=self.CheckModuleFormPost.__name__
    self.__RegisterDef__()
    ModuleName=getattr( self, self.ConfigurationFormName )
    if not hasattr( ModuleName , self.FormPostName ):
      StrErrorMsg = "No Attribute %s, Dict() inside Configuration Class %s" % ( FormPostName , self.ObjectQueryName )
      raise self.Ides.ConfPostDictNotAvailable, StrErrorMsg

  def LoopItemLxmlForm( self ):
    self.FuncName=self.LoopItemLxmlForm.__name__
    self.__RegisterDef__()
    for self.itemForm in self.WebBuffer['lxml'].forms:
      self.LoopItemLxmlInputForm()
  # unchoosen negligee

  def LoopItemLxmlInputForm( self ):
    self.FuncName=self.LoopItemLxmlInputForm.__name__
    self.__RegisterDef__()
    for self.ItemField in self.itemForm.inputs:
      self.QueryDictStruct={ self.ScanHtmlValueWith:self.ItemField.name, self.TransfertHtmlValueWith:self.ItemField.value }
      self.WebBuffer[ self.WebBufferFormKeyName ]['query'].append( self.QueryDictStruct )
      self.QueryAssociation()

  def GetValueAssignFromQueryConf( self ):
    return self.ObjectQueryDict[ self.ItemPostKey ][self.TransfertHtmlValueWith]

  def GetFieldInFormAssign( self ):
    return self.ObjectQueryDict[self.ItemPostKey][self.ScanHtmlValueWith]

  def GetFormLocation( self ):
    return self.ObjectQueryDict[ self.ItemPostKey ][ self.FormLocatorName ]
  
  def QueryAssociation( self ):
    self.FuncName=self.QueryAssociation.__name__
    self.__RegisterDef__()
    ### Will Process Every key inside a QueryConf Object ; Usually a number,

    ### it should not reflect this key anywhere, has long there is natural property inside 
    ### the query serializer having specific writable property like Agent post property. 
    for self.ItemPostKey in self.ObjectQueryDictKeys:
      if self.ScanHtmlValueWith in self.ObjectQueryDict[ self.ItemPostKey ].keys():
        self.WebBuffer['lxml'].forms[ self.GetFormLocation() ].fields[ self.GetFieldInFormAssign() ]=self.GetValueAssignFromQueryConf()
    
  def ParseForm( self ):
    self.FuncName=self.ParseForm.__name__
    self.__RegisterDef__()
    self.LoopItemLxmlForm()
      
  def SendForm( self ):
    self.FuncName=self.SendForm.__name__
    self.__RegisterDef__()
    try:
      Aurl=urllib2.Request( self.WebBuffer['lxml'].forms[0].action )
      ConfirmHost=Aurl.get_host()
    except ValueError:
      Burl=urllib2.Request( self.Url )
      self.WebBuffer['lxml'].forms[0].action = 'http://' + Burl.get_host() + self.WebBuffer['lxml'].forms[0].action

    self.WebBuffer['lxml_result'] = parse( submit_form( self.WebBuffer['lxml'].forms[0] ) ).getroot()

  def __TransitHtmlFile__( self ):
    self.FuncName=self.__TransitHtmlFile__.__name__
    self.__RegisterDef__()
    if os.path.exists( self.FileNameHtmlTransit ):
      print "Removing Existing FileName : %s" % ( self.FileNameHtmlTransit )
      os.remove( self.FileNameHtmlTransit )
    self.FileHandlerHtml=open( self.FileNameHtmlTransit, 'w+' )
    self.FileHandlerHtml.writelines( tostring( self.WebBuffer['lxml_result'] ) )
    self.FileHandlerHtml.close()

  def QueryUrl( self ):
    self.FuncName=self.QueryUrl.__name__
    self.__RegisterDef__()
    if not hasattr( self, self.UrlNameAttr ):
      StrErrorMsg="No Valid %s Attribute found inside object %s" % ( self.UrlNameAttr , self.__class__.__name__ )
      raise self.Ides.NoUrlVariableFound, StrErrorMsg
    if getattr( self, self.UrlNameAttr ).__eq__( '' ):
      StrErrorMsg="Invalid or empty Attribute %s found inside object %s" % ( self.UrlNameAttr , self.__class__.__name__ )
      raise self.Ides.EmptyUrlVariableFound, StrErrorMsg
    self.WebBuffer['buffer']=self.MiniWebBrowser.go( self.Url )

if __name__ == '__main__':
  TestPurposes=True
  LinkClassification=True
  TestObjectReturn=True
  DictSendMaker=True
  PrintLinkRegExrSearch=False
  PrintParamSend=False
  UrlTest='http://www.jobboom.com/fr/ouvrir-une-session'
  UrlQuery=None
  RegExpList=[ re.compile(r'(?ui)fr_CA'),
               re.compile(r'(?ui)QC')  ]
  ATestObj=None

  if TestObjectReturn:
    ATestObj=ObjectReturn( WebObject=pynav.Pynav(),
                           ListRegExp=RegExpList,
                           ListLink=list(),
                           DictValueSendOnPageRequest={ 'UnApiEn':'Python','isAQuestion':'True'},
                           valDict=list( GetListRandSorted( 3, 12 , 3 ) ) )

  if DictSendMaker:
    ATestObj.DictValueSendOnPageRequest.update(
      RandomParamMaker( ATestObj.valDict[0] ,ATestObj.valDict[1] ,ATestObj.valDict[2] ) )
    
  if LinkClassification:
    if PrintParamSend:
      print "Parameter sended : [ %s ] " % ( ATestObj.DictValueSendOnPageRequest )
    FxmlHandler=cStringIO.StringIO( ATestObj.WebObject.go( UrlTest, ATestObj.DictValueSendOnPageRequest ) )
    ATestObj.ListLink=ATestObj.WebObject.get_all_links()
    
    LxmlObj=fromstring( FxmlHandler.read() )
    UrlQuery=GetLinkFromRegExpSpec( ATestObj.ListRegExp , ATestObj.ListLink, ATestObj.DictValueSendOnPageRequest )

  if TestPurposes:
    ATestPurposes=AldderIdes( True,
                              MiniWebBrowser=Pynav(),
                              WebBuffer=dict(),
                              Url=UrlQuery,
                              QueryConf=JobboomConf(),
                              QueryOrderConf=['query'],
                              )
### Prior to keep all thoses line under the __name__.__eq__( '__main__' ), form I invite people 
### trnasforming it into descent class integration function.
### 
