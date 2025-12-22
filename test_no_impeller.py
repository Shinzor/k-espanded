#!/usr/bin/env python3
"""Test Flet desktop with Impeller disabled.

This test sets Flutter engine environment variables to disable Impeller,
which may fix white/blank screen issues on Windows.
"""

import os
import sys

# Disable Impeller rendering engine
# This uses Flutter's engine switch environment variables for Windows
os.environ["FLUTTER_ENGINE_SWITCHES"] = "1"
os.environ["FLUTTER_ENGINE_SWITCH_0"] = "--no-enable-impeller"

# Optional: Also try disabling software rendering issues
# os.environ["FLUTTER_ENGINE_SWITCH_1"] = "--enable-software-rendering"

import flet as ft

def main(page: ft.Page):
    page.title = "No Impeller Test"
    page.window.width = 500
    page.window.height = 400
    page.bgcolor = "#1e1e2e"

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("SUCCESS!", size=32, color="green", weight=ft.FontWeight.BOLD),
                ft.Text("Impeller is DISABLED", size=20, color="yellow"),
                ft.Text("If you can read this, the fix works!", size=14, color="white"),
                ft.Divider(height=20, color="gray"),
                ft.Text("Environment Variables Set:", size=12, color="gray"),
                ft.Text("FLUTTER_ENGINE_SWITCHES=1", size=10, color="gray"),
                ft.Text("FLUTTER_ENGINE_SWITCH_0=--no-enable-impeller", size=10, color="gray"),
                ft.Divider(height=20, color="gray"),
                ft.ElevatedButton("Close", on_click=lambda e: page.window.close()),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(main)
