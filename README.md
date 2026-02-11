# Kuntosalipäiväkirja

Seuraavassa kerrotaan millainen sovellus on ja miten sitä voi testata.

## ***Sovelluksen toiminnot***
- Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen ja ulos sovelluksesta
- Käyttäjä pystyy lisäämään sovellukseen treenejä
- Käyttäjä muokkaamaan lisäämiään treenejä
- Käyttäjä näkee sekä itse lisäämänsä että muiden käyttäjien lisäämät treenit
- Käyttäjä näkee omat ja muiden käyttäjien käyttäjäsivut, josta näkee käyttäjän tekemät treenit
- Kaikki pystyvät etsimään kaikkia treenejä hakusanoilla


## **Miten testata?**
***Sovelluksen asennus***
- Kloonaa sovellus koneellesi avaamalla terminaali ja kirjoita:
```
  git clone https://github.com/jaakseli/Kuntosalipaivakirja.git
```
- Avaa sovellus
```
  $ cd Kuntosalipaivakirja
```
***Luo virtuaaliympäristö ja asenna flask -kirjasto:***
```
 $ python3 -m venv venv
 $ source venv/bin/activate
 $ pip install flask
```
***Luo tietokanta***
```
 $ sqlite3 database.db < schema.sql
```
***Käynnistä sovellus***
```
 $ flask run
```
***Kokeile sovellusta:***
- Luo käyttäjä
- Kirjaudu sisään/ulos
- Lisää treenejä
- Tee hakutoimintoja
