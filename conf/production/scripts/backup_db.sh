#!/bin/bash

timeslot="`date '+%Y%m%d_%H%M'`"
dumpfile="favim_com-${timeslot}.sql"
sharddumpfile="favim_com_shard-${timeslot}.sql"
dumpdir="/tmp/mysql_backup"
LOG="/tmp/dump.log"

echo "`date '+%Y-%m-%d %H:%M:%S'`: Checking temporary directory for mysql dump... " > $LOG
test -d $dumpdir || (echo "`date '+%Y-%m-%d %H:%M:%S'`: Making temporary directory..." >> $LOG && mkdir $dumpdir)

echo "`date '+%Y-%m-%d %H:%M:%S'`: Starting backup of database $dumpfile... " >> $LOG
cd $dumpdir
/usr/bin/mysqldump -F --max-allowed-packet=128M --master-data=2 --single-transaction --ignore-table=favim_com.django_session favim_com > $dumpfile
echo "`date '+%Y-%m-%d %H:%M:%S'`: Done. " >> $LOG

echo "`date '+%Y-%m-%d %H:%M:%S'`: Starting GZIP ${dumpfile} file... " >> $LOG
gzip $dumpfile
echo "`date '+%Y-%m-%d %H:%M:%S'`: Done. " >> $LOG

echo "`date '+%Y-%m-%d %H:%M:%S'`: Move ${dumpfile}.gz to /home/deploy/favim_com/backup_db/ " >> $LOG
mv ${dumpfile}.gz /home/deploy/favim_com/backup_db/


echo "`date '+%Y-%m-%d %H:%M:%S'`: Starting backup of database $sharddumpfile... " >> $LOG
cd $dumpdir
/usr/bin/mysqldump --max-allowed-packet=128M --master-data=2 --single-transaction favim_com_shard > $sharddumpfile
echo "`date '+%Y-%m-%d %H:%M:%S'`: Done. " >> $LOG

echo "`date '+%Y-%m-%d %H:%M:%S'`: Starting GZIP ${sharddumpfile} file... " >> $LOG
gzip $sharddumpfile
echo "`date '+%Y-%m-%d %H:%M:%S'`: Done. " >> $LOG

echo "`date '+%Y-%m-%d %H:%M:%S'`: Move ${sharddumpfile}.gz to /home/deploy/favim_com/backup_db/ " >> $LOG
mv ${sharddumpfile}.gz /home/deploy/favim_com/backup_db/



echo "`date '+%Y-%m-%d %H:%M:%S'`: Copy LOCALES web.favim.com to beta.favim.com/home/deploy/favim_com/backup_locales/ " >> $LOG
rsync -q -av root@web.favim.com:/opt/favim_com/main/locale /home/deploy/favim_com/backup_locales/ >> $LOG
tar -C /home/deploy/favim_com/backup_locales/ -zcvf /home/deploy/favim_com/backup_locales/locales-${timeslot}.tgz locale/ > /dev/null

if [ `date "+%a"` = "Sun" ]; then
    echo "`date '+%Y-%m-%d %H:%M:%S'`: Make hardlink for weekly dump  " >> $LOG
    ln --physical /home/deploy/favim_com/backup_db/${dumpfile}.gz  /home/deploy/favim_com/backup_db/weekly/${dumpfile}.gz
    ln --physical /home/deploy/favim_com/backup_db/${sharddumpfile}.gz  /home/deploy/favim_com/backup_db/weekly/${sharddumpfile}.gz

#    echo "`date '+%Y-%m-%d %H:%M:%S'`: Remove weekly old backups " >> $LOG
    find /home/deploy/favim_com/backup_db/weekly/ -maxdepth 1 -type f -name 'favim_com*.sql.gz'  -mtime +60 -print -delete >> $LOG
fi

#echo "`date '+%Y-%m-%d %H:%M:%S'`: Remove old daily old backups " >> $LOG
find /home/deploy/favim_com/backup_db/ -maxdepth 1 -type f -name 'favim_com*.sql.gz'  -mtime +10 -print -delete >> $LOG
find /home/deploy/favim_com/backup_locales/ -maxdepth 1 -type f -name 'locales-*.tgz' -mtime +15 -print -delete >> $LOG

chown -R deploy: /home/deploy/favim_com/backup_db
chown -R deploy: /home/deploy/favim_com/backup_locales

echo "`date '+%Y-%m-%d %H:%M:%S'`: All jobs finished. Report sent." >> $LOG
cat $LOG | mail -s "[`hostname -f`] Database backup report" root
rm $LOG

exit 0;
