import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Beto's | Flautas y Carne Asada",
  description: "Haz tu pedido de flautas y carne asada para recoger en Calle Oaxaca 2537.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="es"><body>{children}</body></html>;
}
