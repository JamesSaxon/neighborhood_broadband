article       = <au> <year>. \enquote{<title>.} \textit{<journal>} [\textbf{<volume>}][ (<number>):] [<startpage>-<endpage>|<startpage>] ([<month>[ <day>], ]<year>). [<link>] [<note>]
book          = [<au>|<ed>] <year>. \textit{<title>,}[ Vol. <volume>][ <address>:][ <publisher>][, pp.~<startpage>--<endpage>]. [<link>]  [<note>]
chapter       = [<au>] <year>. \enquote{<title>.} In \textit{<booktitle>}[, Vol. <volume>][, <part>][, Ch. <chapter>][, Doc. <document>][, <eds_msg1> <ed>][, pp.~<startpage>--<endpage>].[ <address>:] <publisher>.[<link>]
case          = [<case>, ][<volume>] [<journal>][ <number>] (<year>). [<link> ] [<note>]
statute       = <title>, <congress> Congress, <session> session; <volume> Stat. <page> (<year>). [<link> ] [<note>]
cr            = <journal>, [<congress> Cong., <session> sess.] [Vol <volume>][, pp.~<pages>]. [(<dates>) ][<link> ] [<note>]
data          = <au>, \enquote{<title>.}[ \textit{<publisher>}.] [[Updated <updated>.] Accessed <accessed>.|[<month>[ <day>], ]<year>.] [<link> ][<note>]
inproceedings = <au> <year>. \enquote{<title>,} at \textit{<conference>},[ <address>,][ <startpage>--<endpage>|<startpage>|<eid>] [<link>]
techreport    = [<au>|<ed>] <year>. \textit{<title>.} [Technical Report <number>][ ([<institution>; ][<address>)]][, pp.~<pages>]. [<link>]  [<note>]
website       = <au>[, <institution>], \enquote{<title>.}[ Updated <updated>.] [Accessed [<month>[ <day>], ]<year>.] [<link>]


SPECIAL-TEMPLATES:
authorlist = <author.to_namelist()>
editorlist = <editor.to_namelist()>
authorname.n = <authorlist.n.last>[, <authorlist.n.first.initial()>.][ <authorlist.n.middle.initial()>.][, <authorlist.n.suffix>.]
editorname.n = <editorlist.n.last>[, <editorlist.n.first.initial()>.][ <editorlist.n.middle.initial()>.][, <editorlist.n.suffix>.]
au = <authorname.0>, ...,{ and }<authorname.5>
ed = <editorname.0>, ...,{ and }<editorname.5>
authorlast.n = <authorlist.n.last>
link = [DOI: \href{http://dx.doi.org/<doi>}{<doi>}|\url{<ftp>}|\href{<url>}{\linklogo}|\href{https://scholar.google.com/scholar_case?case=<gsc>}{\linklogo}]
# sortkey = [<authorlist.0.last><year>|<editorlist.0.last><year>|<case><year>|<journal><year>|<key><year>|<congress><year>|<title><year>]
editorlast.n = <editorlist.n.last>
editorshort = <editorlast.0>, ...{ and }<editorlast.0>
label = [{<authorlast.0>, ...{ and }<authorlast.0>}(<year>){<au>}|{<editorshort>}(<year>){<ed>}|{\emph{<case>}}([<volume> ][<journal>][ <number>], <year>)|{<journal>}(<year>)|{<volume> Stat. <page>}(<year>)]
sortkey = <citenum.zfill(3)>              ## order the reference list in the same order as the citations were given in
citelabel = <sortnum>                     ## use numeric reference labels


OPTIONS:
eds_msg1        = edited by 
eds_msg2        = { } eds.
use_citeextract = False
allow_scripts   = True

VARIABLES:
#  citelabel = create_citelabel(entry, options)

DEFINITIONS:
def create_citelabel(entry, options):

    if not "authorlist" in entry:
      return entry["label"]

    numnames = len(entry["authorlist"])
    if numnames == 1:
        s = entry["authorlist"][0]["last"]
    elif numnames == 2:
        s = entry["authorlist"][0]["last"] + " and " + entry["authorlist"][1]["last"]
    else:
        s = entry["authorlist"][0]["last"] + " et al."

    return("{{{:s}}}({:s}){{{:s}}}".format(s, entry["year"], entry["au"]))




