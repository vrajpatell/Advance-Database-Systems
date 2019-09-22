from flask import Flask, render_template, request, redirect
import os
import datetime
import pyodbc
import math
import datetime
app = Flask(__name__)
port = int(os.getenv("PORT", 5000))

server = 'vhpserver.database.windows.net'
database = 'vhpdatabase'
username = 'vrajpatell'
password = 'Vraj0712.'
driver= '{ODBC Driver 17 for SQL Server}'

cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)


@app.route('/')
def index():
    return render_template('form.html')


# This function will retrieve all data for specific magnitude  
@app.route('/countall', methods = ['GET','POST'])
def getnames(name=None):
    
    try:
        if request.method == "POST":
            mag = request.form['mag']
            #connect to db
            conn = ibm_db.connect("DATABASE="+db2cred['db']+";HOSTNAME="+db2cred['hostname']+";PORT="+str(db2cred['port'])+";UID="+db2cred['username']+";PWD="+db2cred['password']+";","","")
            if conn:
                print("in if loop")
                sql='select * from RZG77856.ALL_MONTH where "MAG">?'
                prep = ibm_db.prepare(conn,sql)
                ibm_db.bind_param(prep, 1, mag)
                ibm_db.execute(prep)
                rows = []
                count = 0
                print("conn 2")
            # fetching the result
                result = ibm_db.fetch_assoc(prep)
                while result != False:
                    count = count + 1
                    rows.append(result.copy())
                    result = ibm_db.fetch_assoc(prep)
            # close database connection
                ibm_db.close(conn)
                print("conn 3")
                return render_template('cresult.html', rows=rows, count=count)
            else:
                print("no connection established")
                return render_template('main.html')
    except Exception as e:
        print(e)
        return "<html><body><p>In Exception</p></body></html>"
 
 

#Function for Specified range of magnitudes in given range of days 
@app.route('/getrange', methods = ['GET','POST'])
def getrange():  
    try:
        if request.method == "POST":
            uppermag = request.form['uppermag']
            lowermag = request.form['lowermag']
            startdate = request.form['startdate']
            enddate = request.form['enddate']
            
            #connect to db
            conn = ibm_db.connect("DATABASE="+db2cred['db']+";HOSTNAME="+db2cred['hostname']+";PORT="+str(db2cred['port'])+";UID="+db2cred['username']+";PWD="+db2cred['password']+";","","")
            if conn:
                print("in if loop")
                sql='select * from RZG77856.ALL_MONTH where mag between ? and ? and date >=? and date <=?'
                prep = ibm_db.prepare(conn,sql)
                ibm_db.bind_param(prep, 1, lowermag)
                ibm_db.bind_param(prep, 2, uppermag)
                ibm_db.bind_param(prep, 3, startdate)
                ibm_db.bind_param(prep, 4, enddate)
                ibm_db.execute(prep)
                rows = []
                count = 0
                print("conn 2")
            # fetching the result
                result = ibm_db.fetch_assoc(prep)
                print(result)
                while result != False:
                    count = count + 1
                    rows.append(result.copy())
                    result = ibm_db.fetch_assoc(prep)
            # close database connection
                ibm_db.close(conn)
                print(len(rows))
                return render_template('rangeresult.html', rows=rows, count=count)
            else:
                print("no connection established")
                return render_template('main.html')
    except Exception as e:
        print(e)
        return "<html><body><p>In Exception</p></body></html>"


@app.route('/getdistance', methods = ['GET','POST'])
def getdistance(name=None):  
    try:
        if request.method == "POST":
            lati = request.form['lati']
            longi = request.form['longi']
            dis = request.form['dis']
            #connect to db
            conn = ibm_db.connect("DATABASE="+db2cred['db']+";HOSTNAME="+db2cred['hostname']+";PORT="+str(db2cred['port'])+";UID="+db2cred['username']+";PWD="+db2cred['password']+";","","")
            if conn:
                print("in if loop")
                sql='select * from RZG77856.ALL_MONTH'
                prep = ibm_db.prepare(conn,sql)
                #ibm_db.bind_param(prep, 1, lati)
                #ibm_db.bind_param(prep, 2, longi)
                ibm_db.execute(prep)
                rows = []
                r1 = []
               
                count = 0
                distance = 0
                radius = 6371
                print("conn 2")
            # fetching the result
                result = ibm_db.fetch_assoc(prep)
                while result != False:  
                    
                    rows.append(result.copy())
                    result = ibm_db.fetch_assoc(prep)    
            # close database connection
                ibm_db.close(conn)
               # for row in rows:
                #    distance = (float(row['LATITUDE']) - float(lati))**2 + (float(row['LONGITUDE']) - float(longi))**2 
                 #   d = math.sqrt(distance)*111.2
                    
                #    if(d < float(dis)):
                #        
                #       count = count + 1
                #       r1.append(row)
                
                for row in rows:
                    lat1 = float(lati)
                    lon1 = float(longi)
                    lat2 = float(row['LATITUDE'])
                    lon2 = float(row['LONGITUDE'])
                    dlat = math.radians(lat2 - lat1)
                    dlon = math.radians(lon2 - lon1)
                    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
                        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    d = radius * c
                    if(d < float(dis)):
                        count = count + 1
                        r1.append(row)
                print(count)
                return render_template('distance.html', r1=r1, count = count )
            else:
                print("no connection established")
                return render_template('main.html')
    except Exception as e:
        print(e)
        return "<html><body><p>In Exception</p></body></html>"


@app.route('/night', methods = ['GET','POST'])
def night(name=None):  
         if request.method == "POST":
            magni = request.form['magni']
            #connect to db
            conn = ibm_db.connect("DATABASE="+db2cred['db']+";HOSTNAME="+db2cred['hostname']+";PORT="+str(db2cred['port'])+";UID="+db2cred['username']+";PWD="+db2cred['password']+";","","")
            if conn:
                print("in if loop")
                sql='select * from RZG77856.ALL_MONTH where mag > ? '
                prep = ibm_db.prepare(conn,sql)
                ibm_db.bind_param(prep, 1, magni)
                ibm_db.execute(prep)
                rows = []
                N = 0
                D = 0
                print("conn 2")
            # fetching the result
                result = ibm_db.fetch_assoc(prep)
                while result != False:  
                    rows.append(result.copy())
                    result = ibm_db.fetch_assoc(prep)    
            # close database connection
                ibm_db.close(conn)
                for row in rows:
                    currtime = row['TIME']
                    currdate = row['DATE']
                    longit = float(row['LONGITUDE'])
                    tdiff = (int(longit*24)/360)
                    diff = datetime.datetime.combine(currdate, currtime) - datetime.timedelta(hours=tdiff)
                    if(diff.time().hour < 8 or diff.time().hour > 20):
                        N = N + 1
                    else:
                        D = D + 1
                  
                return render_template('daynight.html', N = N, D = D )
            else:
                print("no connection established")
                return render_template('main.html')
    
@app.route('/clustring', methods = ['GET','POST'])
def clustring(name=None):  
        if request.method == "POST":
            lati1 = request.form['lati1']
            long1 = request.form['long1']
            lati2 = request.form['lati2']
            long2 = request.form['long2']
            kcul = request.form['kcul']
            
            #latlon = []
            lati1 = int(float(lati1))
            lati2 = int(float(lati2))
            long1 = int(float(long1))
            long2 = int(float(long2))
            kcul = int(kcul)
            
            #connect to db
            conn = ibm_db.connect("DATABASE="+db2cred['db']+";HOSTNAME="+db2cred['hostname']+";PORT="+str(db2cred['port'])+";UID="+db2cred['username']+";PWD="+db2cred['password']+";","","")
            if conn:
                print("in if loop")
                latrange = []
                lonrange = []
                countl = []
                counter = 0
               
                for i in range(lati1, lati2, -kcul):
                    print("1st Loop")
                    for j in range(long1,long2, kcul):
                        
                        nolat = i - kcul
                        nolon = j + kcul
                        sql='select count(*) from RZG77856.ALL_MONTH where latitude between ? and ? and longitude between ? and ?'
                        prep = ibm_db.prepare(conn,sql)
                        ibm_db.bind_param(prep, 1, nolat)
                        ibm_db.bind_param(prep, 2, i) 
                        
                        ibm_db.bind_param(prep, 3, j)
                        ibm_db.bind_param(prep, 4, nolon)
                        ibm_db.execute(prep)
                    
                        result = ibm_db.fetch_assoc(prep)
                        
                        count = result.copy()
                     
                        countl.append(int(count['1']))
                        latrange.append(i)
                        lonrange.append(j)
                  
                ibm_db.close(conn)      
                lengthcounter = len(latrange)
                print("outside loop")           
                return render_template('clustering.html', lengthcounter = lengthcounter, latrange = latrange, lonrange = lonrange, countl = countl )
            else:
                print("no connection established")
                return render_template('main.html')
    



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
