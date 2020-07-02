import numpy as np
import cv2
import imutils
import sys
import pytesseract
from tkinter import *
from tkinter import messagebox
import pandas as pd
import time
import sqlite3
import random
import datetime

TESSDATA_PREFIX = 'C:/Program Files (x86)/Tesseract-OCR'
video = cv2.VideoCapture("plakavideo.mp4")
# VERİ TABANI BAĞLANTISI
con = sqlite3.connect("arabaPlaka.db")
cursor = con.cursor()
#TKİNTER ARAYÜZ
pencere = Tk()
pencere.title("Plaka Tanıma Sistemi")
pencere.geometry("500x1000")

# formu grid olarak çizdirme /layout düzeni
uygulama = Frame(pencere, )
uygulama.grid()

listbox = Listbox(uygulama)
#listaboxı tanıtma

def main():
    s = 1
    while True:
        ret, resim = video.read()
        resim = imutils.resize(resim, width=500)
        gray = cv2.cvtColor(resim, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        edged = cv2.Canny(gray, 170, 200)
        (cnts, _) = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)  # removed new
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]
        NumberPlateCnt = None
        count = 0
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                NumberPlateCnt = approx
                break
        # Plaka dışındaki parçayı maskeleme
        mask = np.zeros(gray.shape, np.uint8)
        Sresim = cv2.drawContours(mask, [NumberPlateCnt], 0, 255, -1)
        Sresim = cv2.bitwise_and(resim, resim, mask=mask)
        cv2.namedWindow("Plaka", cv2.WINDOW_NORMAL)
        cv2.imshow("Plaka", Sresim)
        # Tesseract için yapılandırma, resimdeki harfleri tanımlıyor
        config = ('-l eng --oem 1 --psm 3')
        # Görüntü üzerinde tesseract OCR çalıştır
        text = pytesseract.image_to_string(Sresim, config=config)
        print(text)
        plaka = str(text)

        def update():
            #OKUNAN PLAKANIN GİRİŞ ÇIKIŞ SAATİNİ GÜNCELLEME

            cursor.execute("SELECT Durum FROM Kontrol WHERE Plaka='{}' ".format(plaka))
            upt = cursor.fetchall()#durum bilgisini çekiyor
            print(upt)
            for i in upt:
                st = str(i)#durumu stringe çeviriyor
                zaman = time.time()
                tarih = str(datetime.datetime.utcfromtimestamp(zaman).strftime('%Y-%m-%d %H:%M:%S'))#okunduğu zaman tarihi alıyor
                if (st == "(1,)"):
                    cursor.execute("UPDATE Kontrol SET Durum=0 WHERE Plaka='{}' ".format(plaka))
                    cursor.execute("UPDATE Kontrol SET C_tarih='{}' ".format(tarih) + " WHERE Plaka='{}' ".format(plaka))
                    Kapi = Label(uygulama, text="Çıkış Yapıldı. ", font=("Ariel", 12))
                    Kapi.grid(row=1, column=0, padx=155, sticky=W, pady=5, columnspan=2)#konumlandırılması

                elif (st == "(0,)"):
                    cursor.execute("UPDATE Kontrol SET Durum=1 WHERE Plaka='{}' ".format(plaka))
                    cursor.execute("UPDATE Kontrol SET G_tarih='{}' ".format(tarih) + " WHERE Plaka='{}' ".format(plaka))
                    Kapi = Label(uygulama, text="Giriş Yapıldı. ", font=("Ariel", 12)) #uygulama frame
                    Kapi.grid(row=1, column=0, padx=155, sticky=W, pady=5, columnspan=2)

                else:
                    print("Plaka tanımlı değil.")
                    Kapi = Label(uygulama, text="Plaka Kayıtlı Değil. ", font=("Ariel", 12))
                    Kapi.grid(row=1, column=0, padx=155, sticky=W, pady=5, columnspan=2)
                con.commit()

        # Data CSV dosyasında saklanır.
        if text:
            #OKUNAN ARACI TKİNDERDA GÖSTERME
            O_plaka = Label(uygulama, text="Araç: " + plaka, font=("Ariel", 15, "bold"), foreground="#b10000")
            O_plaka.grid(row=0, column=0, padx=150, sticky=W, pady=2, columnspan=2)

            update()
            """EXCELE GENEL KAYIT
            raw_data = {'date': [time.asctime(time.localtime(time.time()))], '': [text]}
            df = pd.DataFrame(raw_data)
            df.to_csv('data.csv', mode='a')
            print("excel kaydı başarılı")"""
        else:
            Kapi = Label(uygulama, text="Plaka Kayıtlı Değil. ", font=("Ariel", 12))
            Kapi.grid(row=1, column=0, padx=155, sticky=W, pady=5, columnspan=2)
        s = s - 1
        if s == 0:
            break

    cv2.waitKey(0)
    cv2.destroyAllWindows()

    def listele():
        #TÜM ARAÇLARI LİSTELE
        listbox.delete(0, END)
        cursor.execute("SELECT * FROM Kontrol")
        data = cursor.fetchall()# VERİTABANINDAKİ TÜMVERİLERİ ÇEKİYOR
        a=0
        for i in data:
            a += 1
            listbox.insert(a, i)
            listbox.grid(row=10,column=0, padx=2, ipadx=150, ipady=2)

        def excelListe():
            for i in data:
                # EXCELE GENEL KAYIT
                raw_data = {'Tarih': [time.asctime(time.localtime(time.time()))], '': [i]}
                df = pd.DataFrame(raw_data)
                df.to_csv('liste.csv', mode='a')
            print("excel kaydı başarılı")
            messagebox.showinfo("Bilgi","Kayıt Başarılı.")

        excelRapor = Button(uygulama, bg="#b10000", text=" EXCEL ",font=("Ariel", 9, "bold"),fg="#f2f2f2", width=14, height=1, command=excelListe)
        excelRapor.grid(row=15, column=0, padx=150, pady=2)

    def tarihListele():
        #GİRİLEN TARİHE GÖRE LİSTELE
        listbox.delete(0, END)
        nTarih = tL.get()
        if(nTarih):
            cursor.execute("SELECT * FROM Kontrol WHERE G_tarih BETWEEN '"+nTarih+" 00:00:00' AND '"+nTarih+"23:59:59'")
            data = cursor.fetchall()
            a=0
            if(data):
                for i in data:
                    a += 1
                    listbox.insert(a, i)
                    listbox.grid(row=10, ipadx=150, ipady=2)
            else:
                messagebox.showinfo("Uyarı", "Lütfen Tarihi YYYY-AA-GG Formatında giriniz!")
        else:
            messagebox.showinfo("Uyarı", "Lütfen Tarihi Giriniz!")
    def plakaListele():
        #PLAKAYA GÖRE LİSTELE
        listbox.delete(0, END)
        nPlaka = pL.get()
        if(nPlaka):
            cursor.execute("SELECT * FROM Kontrol WHERE Plaka ='"+nPlaka+"'" )
            data = cursor.fetchall()
            if(data):
                listbox.insert(1, data)
                listbox.grid(row=10, ipadx=150, ipady=2)
            else:
                messagebox.showinfo("Uyarı", "Plaka bulunamadı. Lütfen Plakayı Kontrol Ediniz!")

        else:
            messagebox.showinfo("Uyarı", "Lütfen Plakayı Giriniz!")
    def iceri():
        # İÇERİDEKİ ARAÇLARI LİSTELE
        listbox.delete(0, END)
        cursor.execute("SELECT * FROM Kontrol WHERE Durum=1")
        data = cursor.fetchall()
        a = 0
        for i in data:
            a += 1
            listbox.insert(a, i)
            listbox.grid(row=10, column=0, padx=2, ipadx=150, ipady=2)


    def Kayit():
        def Kaydet():
            N_plaka = e1.get()
            N_ad = e2.get()
            N_soyad = e3.get()
            print(N_plaka, N_ad, N_soyad)
            Kaydi = Label(uygulama, text=N_plaka + " " + N_ad + "" + N_soyad)
            Kaydi.grid(row=16, column=0, padx=20, pady=2)
            G_tarih = ""
            C_tarih = ""
            Ad = N_ad
            Soyad = N_soyad
            Plaka = N_plaka
            Durum = True
            cursor.execute("INSERT INTO Kontrol(Plaka,Ad,Soyad,G_tarih,C_tarih,Durum) VALUES(?,?,?,?,?,?)",
                           (Plaka, Ad, Soyad, G_tarih, C_tarih, Durum))
            con.commit()

        # this will create a label widget
        l1 = Label(uygulama, text="Plaka: ", font=("Ariel", 10, "bold"))
        l2 = Label(uygulama, text="Ad: ", font=("Ariel", 10, "bold"))
        l3 = Label(uygulama, text="Soyad: ", font=("Ariel", 10, "bold"))

        # grid method to arrange labels in respective
        # rows and columns as specified
        l1.grid(row=12, column=0, sticky=W, pady=2, padx=60)
        l2.grid(row=13, column=0, sticky=W, pady=2, padx=60)
        l3.grid(row=14, column=0, sticky=W, pady=2, padx=60)
        # entry widgets, used to take entry from user
        e1 = Entry(uygulama)
        e2 = Entry(uygulama)
        e3 = Entry(uygulama)
        # this will arrange entry widgets
        e1.grid(row=12, column=0, pady=2)
        e2.grid(row=13, column=0, pady=2)
        e3.grid(row=14, column=0, pady=2)

        buton = Button(uygulama)
        buton.config(text=u"Kaydet", bg="#b10000",fg="#f2f2f2",font=("Ariel", 10, "bold"), command=Kaydet)
        buton.grid(row=15, column=0, padx=10, pady=2)

    #---------------------- LİSTELEME BUTONLARI---------------------
    TumunuListele = Button(uygulama, bg="#b10000", text=" Araçları Listele ",font=("Ariel", 9, "bold"),fg="#f2f2f2", width=14, height=1, command=listele)
    TumunuListele.grid(row=3, column=0, padx=155, pady=5)
    iceridekiler = Button(uygulama, bg="#b10000", text=" İçerideki Araçlar ", font=("Ariel", 9, "bold"), fg="#f2f2f2",width=14, height=1, command=iceri)
    iceridekiler.grid(row=4, column=0, padx=155, pady=5)
    PlakaLabel = Label(uygulama, text="Plaka: ",width=12, height=1, font=("Ariel", 10, "bold")).grid(row=5, column=0, sticky=W, pady=2, padx=60)
    pL = Entry(uygulama)
    pL.grid(row=5, column=0, pady=2, padx=155)
    PlakaListele = Button(uygulama, font=("Ariel", 9), bg="#b10000",fg="#f2f2f2")
    PlakaListele.config(text="Listele ", width=12, height=1, command=plakaListele)
    PlakaListele.grid(row=6, column=0, pady=20, padx=155)

    TarihLabel = Label(uygulama, text="Tarih: ", width=12, height=1, font=("Ariel", 10, "bold")).grid(row=7, column=0, sticky=W, pady=2, padx=60)
    tL = Entry(uygulama)
    tL.grid(row=7, column=0, pady=2, padx=155)
    TarihListele = Button(uygulama, font=("Ariel", 9), bg="#b10000",fg="#f2f2f2")
    TarihListele.config(text=u"Listele ", width=12, height=1, command=tarihListele)
    TarihListele.grid(row=8, column=0, pady=2, padx=155)



    menubar = Menu(pencere)
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Araç Kaydet", command=Kayit)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=pencere.quit)
    menubar.add_cascade(label="File", menu=filemenu)

    pencere.config(menu=menubar)
    #TKİNTER PENCERESİNİ KAPATTIK
    pencere.mainloop()

if __name__ == "__main__":
    main()
con.close()


