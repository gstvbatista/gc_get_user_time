#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Official repo https://github.com/gstvbatista/gc_get_user_time
#
# Copyright (C) 2025
#
# This file is part of https://github.com/gstvbatista/gc_get_user_time.
#
# This software is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/>.

import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import threading
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable
import logging

from purecloud_api import PureCloudAPI

logging.basicConfig(level=logging.INFO)

def process_users(user_logins: List[str], start_date: datetime, end_date: datetime,
                  progress_callback: Callable[[int, str], None]) -> List[Dict[str, Any]]:
    """
    Processa a obtenção dos dados para os usuários informados, atualizando o progresso via callback.
    progress_callback: função que recebe (percent: int, message: str)
    """
    progress_callback(0, "Iniciando o processo...")
    api = PureCloudAPI()
    
    progress_callback(5, "Autenticando na API do Genesys Cloud...")
    access_token = api.get_oauth_token()
    if not access_token:
        raise Exception("Não foi possível obter o token de acesso.")
    
    progress_callback(15, "Obtendo a lista de usuários...")
    users = api.get_users(access_token)
    if not users:
        raise Exception("Não foi possível obter a lista de usuários.")
    
    # Cria um índice de usuários
    user_index = {}
    for user in users:
        key = user.get("email", "").split("@")[0].lower()
        user_index[key] = user

    progress_callback(20, "Lista de usuários obtida. Iniciando processamento individual...")
    valid_logins = [login for login in user_logins if login.lower() in user_index]
    total_valid = len(valid_logins)
    if total_valid == 0:
        raise Exception("Nenhum login informado foi encontrado na lista de usuários da API.")

    all_rows: List[Dict[str, Any]] = []
    processed = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_login = {}
        for login in valid_logins:
            future = executor.submit(api.get_user_time, access_token, user_index[login.lower()], start_date, end_date)
            future_to_login[future] = login
        for future in as_completed(future_to_login):
            login = future_to_login[future]
            try:
                rows = future.result()
                all_rows.extend(rows)
                processed += 1
                percent = 20 + int((processed / total_valid) * 80)
                progress_callback(percent, f"Processado usuário: {login} ({processed} de {total_valid})")
            except Exception as e:
                logging.exception(f"Erro ao processar o usuário {login}: {e}")
                processed += 1
                percent = 20 + int((processed / total_valid) * 80)
                progress_callback(percent, f"Erro ao processar o usuário: {login} ({processed} de {total_valid})")
    return all_rows

def save_csv(data: List[Dict[str, Any]], file_path: str) -> None:
    fieldnames = [
        "DATE", "USER_ID", "USER_EMAIL", "LOGGED_IN", "ON_QUEUE", "OFF_QUEUE",
        "INTERACTING", "IDLE", "NOT_RESPONDING", "AVAILABLE", "AWAY", "BREAK",
        "BUSY", "SYSTEM_AWAY", "MEAL", "MEETING", "TRAINING"
    ]
    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for row in data:
            writer.writerow(row)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Genesys Cloud - Coleta de Tempos")
        self.geometry("580x560")
        self.resizable(False, False)

        instructions = ("Instruções\n"
                        "- Informe as datas (DD/MM/AAAA) onde a data final não pode ser anterior à data início.\n"
                        "- Informe os logins dos usuários (um por linha).")
        self.label_instructions = tk.Label(self, text=instructions, wraplength=580, justify="left")
        self.label_instructions.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="w")

        self.label_start = tk.Label(self, text="Data Início")
        self.label_start.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.entry_start = tk.Entry(self)
        self.entry_start.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        self.label_end = tk.Label(self, text="Data Final")
        self.label_end.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.entry_end = tk.Entry(self)
        self.entry_end.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        self.label_users = tk.Label(self, text="Lista de Usuários")
        self.label_users.grid(row=3, column=0, padx=10, pady=5, sticky="ne")
        self.text_users = tk.Text(self, height=10, width=50)
        self.text_users.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        self.scrollbar_users = tk.Scrollbar(self, orient="vertical", command=self.text_users.yview)
        self.text_users.configure(yscrollcommand=self.scrollbar_users.set)
        self.scrollbar_users.grid(row=3, column=2, sticky="ns", padx=(0,10), pady=5)

        self.button_process = tk.Button(self, text="Processar", command=self.on_process)
        self.button_process.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        self.progress_bar = ttk.Progressbar(self, orient="horizontal", mode="determinate", maximum=100, length=400)
        self.progress_bar.grid(row=5, column=1, padx=10, pady=5)
        self.progress_bar["value"] = 0

        self.label_status = tk.Label(self, text="", fg="blue")
        self.label_status.grid(row=6, column=1, padx=10, pady=5)

        self.label_log = tk.Label(self, text="Log")
        self.label_log.grid(row=7, column=0, padx=10, pady=5, sticky="nw")
        self.text_log = tk.Text(self, height=5, width=50, state="disabled")
        self.text_log.grid(row=7, column=1, padx=10, pady=5, sticky="w")
        self.scrollbar_log = tk.Scrollbar(self, orient="vertical", command=self.text_log.yview)
        self.text_log.configure(yscrollcommand=self.scrollbar_log.set)
        self.scrollbar_log.grid(row=7, column=2, sticky="ns", padx=(0,10), pady=5)

    def log_message(self, message: str):
        self.text_log.config(state="normal")
        self.text_log.insert(tk.END, message + "\n")
        self.text_log.see(tk.END)
        self.text_log.config(state="disabled")

    def update_progress(self, percent: int, message: str):
        self.progress_bar["value"] = percent
        self.label_status.config(text=message)
        self.log_message(message)
        self.update_idletasks()

    def on_process(self):
        start_date_str = self.entry_start.get().strip()
        end_date_str = self.entry_end.get().strip()
        users_text = self.text_users.get("1.0", tk.END)

        try:
            start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
            end_date = datetime.strptime(end_date_str, "%d/%m/%Y")
            if end_date < start_date:
                messagebox.showerror("Erro", "A data final não pode ser anterior à data de início.")
                return
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido. Utilize DD/MM/YYYY.")
            return

        user_logins = [line.strip() for line in users_text.splitlines() if line.strip()]
        if not user_logins:
            messagebox.showerror("Erro", "Informe pelo menos um login de usuário.")
            return

        self.button_process.config(state=tk.DISABLED)
        self.update_progress(0, "Processando, por favor aguarde...")

        threading.Thread(target=self.process_thread, args=(user_logins, start_date, end_date), daemon=True).start()

    def process_thread(self, user_logins: List[str], start_date: datetime, end_date: datetime):
        try:
            data = process_users(user_logins, start_date, end_date, self.thread_progress_callback)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            self.after(0, lambda: self.button_process.config(state=tk.NORMAL))
            self.after(0, lambda: self.update_progress(0, ""))
            return

        default_filename = f"{start_date.strftime('%d%m%Y')}-{end_date.strftime('%d%m%Y')}.csv"
        file_path = filedialog.asksaveasfilename(title="Salvar CSV", defaultextension=".csv",
                                                 initialfile=default_filename, filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                save_csv(data, file_path)
                self.after(0, lambda: messagebox.showinfo("Sucesso", f"Arquivo salvo em: {file_path}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", f"Erro ao salvar CSV: {e}"))
        self.after(0, lambda: self.button_process.config(state=tk.NORMAL))
        self.after(0, lambda: self.update_progress(100, "Processo concluído."))

    def thread_progress_callback(self, percent: int, message: str):
        self.after(0, lambda: self.update_progress(percent, message))

if __name__ == "__main__":
    app = App()
    app.mainloop()
