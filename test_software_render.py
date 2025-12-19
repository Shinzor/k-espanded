#!/usr/bin/env python3
"""Test Flet desktop with software rendering (SwiftShader).

This test forces software rendering which bypasses GPU issues.
"""

import os
import sys

# Force ANGLE to use SwiftShader (software rendering)
os.environ["ANGLE_DEFAULT_PLATFORM"] = "swiftshader"

# Also try disabling Impeller
os.environ["FLUTTER_ENGINE_SWITCHES"] = "2"
os.environ["FLUTTER_ENGINE_SWITCH_0"] = "--no-enable-impeller"
os.environ["FLUTTER_ENGINE_SWITCH_1"] = "--enable-software-rendering"

import flet as ft

def main(page: ft.Page):
    page.title = "Software Rendering Test"
    page.window.width = 500
    page.window.height = 400
    page.bgcolor = "#1e1e2e"

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("SUCCESS!", size=32, color="green", weight=ft.FontWeight.BOLD),
                ft.Text("Software Rendering Mode", size=20, color="yellow"),
                ft.Text("If you can read this, software rendering works!", size=14, color="white"),
                ft.Divider(height=20, color="gray"),
                ft.Text("Settings Applied:", size=12, color="gray"),
                ft.Text("ANGLE_DEFAULT_PLATFORM=swiftshader", size=10, color="gray"),
                ft.Text("--no-enable-impeller", size=10, color="gray"),
                ft.Text("--enable-software-rendering", size=10, color="gray"),
                ft.Divider(height=20, color="gray"),
                ft.ElevatedButton("Close", on_click=lambda e: page.window.close()),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(main)
