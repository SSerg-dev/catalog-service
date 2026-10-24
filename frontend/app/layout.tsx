import type { Metadata } from "next";
import type { ReactNode } from "react";

import { TelegramBridge } from "../components/telegram-bridge";
import "./styles.css";


export const metadata: Metadata = {
  title: "Каталог",
  description: "Каталог товаров",
};


export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <TelegramBridge />
        {children}
      </body>
    </html>
  );
}

