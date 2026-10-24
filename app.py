from flask import Flask, render_template, redirect, url_for, session, request
import smtplib
from email.message import EmailMessage
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from validador import *
import secrets
import time
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ["SECRET_KEY"]

EMAIL_BOT = os.environ["EMAIL_BOT"]
EMAIL_SENHA = os.environ["EMAIL_SENHA"]


class Banco:
    def __init__(self, banco):
        self.bancoName = banco
        self.banco = None

    def abrirBanco(self):
        self.banco = sqlite3.connect(self.bancoName)
        cursor = self.banco.cursor()

        return cursor

    def fecharBanco(self):
        self.banco.commit()
        self.banco.close()



@app.route("/")
def main():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        banco = Banco("BancoDados.db")
        cursor = banco.abrirBanco()

        password = request.form.get("senha")
        email = request.form.get("email").strip().lower()

        if not email or not password:
            banco.fecharBanco()
            return render_template("login.html", msg="Não deixa os Espaços em branco!")

        if not validar_dado(EmailValidador(), email):
            banco.fecharBanco()
            return render_template("login.html", msg="Email Invalido!")

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))

        resultado = cursor.fetchone()

        if not resultado:
            banco.fecharBanco()
            return render_template("login.html", msg="Senha ou Email Invalido!")

        if check_password_hash(resultado[2], password):
            banco.fecharBanco()
            session["ID"] = resultado[0]
            return redirect(url_for("dashboard"))

        banco.fecharBanco()
        return render_template("login.html", msg="Senha ou Email Invalido!")
    return render_template("login.html", msg=" ")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        banco = Banco("BancoDados.db")
        cursor = banco.abrirBanco()

        password = request.form.get("password")
        email = request.form.get("email").strip().lower()
        nome = request.form.get("nome")

        if not password or not email or not nome:
            banco.fecharBanco()
            return render_template("register.html", msg="Não deixe nenhum espaço em Branco!")

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))

        resposta = cursor.fetchone()

        if resposta:
            banco.fecharBanco()
            return render_template("register.html", msg="Email já Existente!")

        if not validar_dado(EmailValidador(), email):
            banco.fecharBanco()
            return render_template("register.html", msg="Email Invalido!")

        if not validar_dado(SenhaValidador(), password):
            banco.fecharBanco()
            return render_template("register.html", msg="Senha Muito Fraca!")

        senhaCriptografada = generate_password_hash(password)

        cursor.execute("INSERT INTO users (email, senha, nome) VALUES (?, ?, ?)", (email, senhaCriptografada, nome))
        banco.fecharBanco()

        return redirect(url_for("login"))

    return render_template("register.html", msg=" ")

@app.route("/recuperacao", methods=["GET", "POST"])
def recuperacao():

    if request.method == "POST":

        banco = Banco("BancoDados.db")
        cursor = banco.abrirBanco()
        
        email = request.form.get("email").strip().lower()

        if not email:
            banco.fecharBanco()
            return render_template("recuperacao.html", msg="Preencha o espaço em Branco!")

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))

        resultado = cursor.fetchone()

        session.clear()

        if resultado:
            codigoRecuperacao = str(secrets.randbelow(900000) + 100000)
            codigoCriptografado = generate_password_hash(codigoRecuperacao)

            bancoReset = Banco("PassWords_reset.db")
            cursor2 = bancoReset.abrirBanco()

            cursor2.execute("DELETE FROM passwords_reset WHERE email = ?",(email,))
            cursor2.execute("INSERT INTO passwords_reset (email, tentativas, codigo) VALUES (?, ? ,?)", (resultado[1], 0, codigoCriptografado))

            session["RecuperationEmail"] = resultado[1]
            email = EmailMessage()
            email["From"] = EMAIL_BOT
            email["To"] = resultado[1]
            email["Subject"] = "Recuperação De Senha"
            email.set_content(f"Seu código de recuperação é {codigoRecuperacao}")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
                servidor.login(EMAIL_BOT, EMAIL_SENHA)
                servidor.send_message(email)

            banco.fecharBanco()
            bancoReset.fecharBanco()
            return redirect(url_for("code"))

        banco.fecharBanco()
        return render_template("recuperacao.html", msg="Se o emai estiver Cadastrado, você recebera informações!")

    return render_template("recuperacao.html", msg=" ")

@app.route("/recuperacao/code", methods=["GET", "POST"])
def code():

    if not "RecuperationEmail" in session:
        return redirect(url_for("recuperacao"))

    if request.method == "POST":

        bancoReset = Banco("PassWords_reset.db")
        cursor = bancoReset.abrirBanco()

        cursor.execute("SELECT * FROM passwords_reset WHERE email = ?", (session["RecuperationEmail"],))

        resultado = cursor.fetchone()

        if not resultado:
            session.clear()
            bancoReset.fecharBanco()
            return redirect(url_for("recuperacao"))

        if resultado[2] == 2:
            session.clear()
            bancoReset.fecharBanco()
            return redirect(url_for("recuperacao"))

        codigo = request.form.get("codigo")

        if not codigo:
            bancoReset.fecharBanco()
            return render_template("recuperacaoCode.html", msg="Preencha o espaço em branco!")

        if check_password_hash(resultado[3], codigo):
            session["ResetToken"] = secrets.token_urlsafe(32)
            session["ResetTokenExpiracao"] = time.time() + 300
            bancoReset.fecharBanco()
            return redirect(url_for("resetPassword"))

        calculo = resultado[2] + 1

        cursor.execute("UPDATE passwords_reset SET tentativas = ? WHERE email = ?", (calculo, session["RecuperationEmail"]))
        bancoReset.fecharBanco()
        return render_template("recuperacaoCode.html", msg="Codigo Incorreto!")

    return render_template("recuperacaoCode.html", msg=" ")


@app.route("/recuperacao/code/Sucessful", methods=["POST", "GET"])
def resetPassword():

    token = session.get("ResetToken")
    expiracao = session.get("ResetTokenExpiracao")
    RecuperationEmail = session.get("RecuperationEmail")

    if not RecuperationEmail or not token or not expiracao or time.time() >= expiracao:
        bancoReset = Banco("PassWords_reset.db")
        cursor2 = bancoReset.abrirBanco()
        if RecuperationEmail:
            cursor2.execute("DELETE FROM passwords_reset WHERE email = ?", (RecuperationEmail,))
        session.pop("ResetToken", None)
        session.pop("ResetTokenExpiracao", None)
        session.pop("RecuperationEmail", None)
        bancoReset.fecharBanco()

        return redirect(url_for("recuperacao"))
    else:
        if request.method == "POST":
            password = request.form.get("password")
            passwordConfirm = request.form.get("confirmar_password")

            if password == passwordConfirm:
                banco = Banco("BancoDados.db")
                cursor = banco.abrirBanco()

                bancoReset = Banco("PassWords_reset.db")
                cursor2 = bancoReset.abrirBanco()

                if not validar_dado(SenhaValidador(), password):
                    return render_template("ResetPassword.html", msg="A senha é Muito Fraca!")

                senhaHash = generate_password_hash(password)

                cursor.execute("UPDATE users SET senha = ? WHERE email = ?", (senhaHash, session["RecuperationEmail"]))

                cursor2.execute("DELETE FROM passwords_reset WHERE email = ?", (session["RecuperationEmail"],))
                
                banco.fecharBanco()
                bancoReset.fecharBanco()

                session.clear()
                return redirect(url_for("login"))
            
            return render_template("ResetPassword.html", msg="As senhas não são Iguais!")

        return render_template("ResetPassword.html", msg=" ")


@app.route("/dashboard")
def dashboard():
    return "logado pae"

if __name__ == "__main__":
    app.run(debug=True)
