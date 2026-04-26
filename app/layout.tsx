import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Defensor — Defensoría legal de pacientes",
  description:
    "Defensor lee tu documento de atención denegada, identifica qué artículo de la ley se violó y redacta tu reclamo formal.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
