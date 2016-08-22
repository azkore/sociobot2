import sqlite3
import config

def to_seconds(time):
    switcher= {
            'h': 60*60,
            'm': 60,
            'd': 24*60*60,
            's': 1
            }

    if(time[-1] in switcher.keys()):
        res=int(time[:-1])*switcher[time[-1]]
    else:
        res=time
    return res

def get_soctype(soctype, active):

    rows=sql(("select soctypes.firstname from soctypes, users"
        " where soctypes.type=?"
        " and soctypes.user=users.uid"
        " and (strftime('%s', 'now') - users.seen) < ?;"), (soctype, int(active)))


    res=[]
    for row in rows:
        res.append(row[0])
    print("res" + str(res))
    return res

def get_soctypes(soctype='', active=3600):
    soctypes=('дон','дюма', 'гюго', 'роб', 'гам', 'макс', 'жук', 'еся', 'нап','баль', 'джек', 'драй', 'штир', 'дост', 'гек', 'габ')
    res=''
    total=0

    quadras=['α','ϐ','γ','δ']
    if soctype:
        members=get_soctype(soctype, active=active)
        print(str(members))
        res='(<b>'+str(len(members))+'</b>) '+ plist(members)
    else:
        i=0
        for type in soctypes:
            members=get_soctype(type, active=active)
            if(i%4==0):
                q=int(i/4)
                print(q)
                qtot=0
                res=res+"<b>• "+quadras[q]+"</b>\n"
            if(members):
                res=res+"    <b>{} ({})</b>: {}\n".format(type.upper(), str(len(members)), plist(members))
           
            i=i+1
            total=total+len(members)
            qtot=qtot+len(members)
            if(i%4==0):
                res=res.replace(quadras[q], quadras[q]+" ("+str((qtot))+")")
        chebs=get_chebu(active)
        res=res+'<b>Чебурашки({}):</b> {}\n'.format(len(chebs), plist(chebs))
        total=total+len(chebs)
        res=res+'Всего: <b>{}</b>'.format(str(total))
    return res

def get_chebu(active):
    rows=sql("select firstname from users"
        " where users.uid not in (select user from soctypes)"
        " and firstname!=''"
        " and (strftime('%s', 'now') - users.seen) < ?;", (active,))
    res=[]
    for row in rows:
        res.append(row[0])
    return res

def plist(l):
    res=''
    print(l)
    for i in l:
        res=res + i + ", "
        
    return res.strip(', ')

def sql(sql, params=() ):
    db=sqlite3.connect(config.db)
    db.enable_load_extension(True)
    db.load_extension("libsqliteicu")
    with db:
        c=db.cursor()
        print(sql, params)
        c.execute(sql, params)
        res=c.fetchall()
    return res

def select(column, table, params=() ):
    res=list(map(lambda row: row[0], sql("select {} from {}".format(column, table), params )))
    if(res):
        return res
    else:
        return ["нет результатов"]
