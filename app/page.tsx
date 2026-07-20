"use client";

import { useMemo, useState } from "react";

type Item = { id: string; name: string; description?: string; price: number; section: "flautas" | "asada" };

const items: Item[] = [
  { id: "f-carne", name: "Flauta de carne", description: "Crujiente, sabrosa y hecha con orgullo", price: 45, section: "flautas" },
  { id: "f-papa", name: "Flauta de papa", description: "Dorada al momento", price: 40, section: "flautas" },
  { id: "soda", name: "Soda", price: 29, section: "flautas" },
  { id: "cueritos", name: "Cueritos", price: 10, section: "flautas" },
  { id: "guacamole", name: "Guacamole extra", price: 10, section: "flautas" },
  { id: "salsa", name: "Salsa extra", price: 10, section: "flautas" },
  { id: "crema", name: "Crema extra", price: 10, section: "flautas" },
  { id: "kg-carne", name: "1 kg de carne asada", description: "Papa, cebolla, tortillas y chiles toreados", price: 400, section: "asada" },
  { id: "medio-carne", name: "½ kg de carne asada", description: "Papa, cebolla, tortillas y chiles toreados", price: 250, section: "asada" },
  { id: "plato-carne", name: "Platillo individual", description: "250 g de carne con papa, cebolla, tortillas y chiles", price: 150, section: "asada" },
  { id: "kg-costilla", name: "1 kg de costilla", description: "Papa, cebolla, tortillas y salsas", price: 300, section: "asada" },
  { id: "medio-costilla", name: "½ kg de costilla", description: "Papa, cebolla, tortillas y salsa", price: 200, section: "asada" },
  { id: "plato-costilla", name: "Platillo individual de costilla", description: "250 g con papa, cebolla, tortillas y chiles", price: 120, section: "asada" },
  { id: "soda-asada", name: "Soda", price: 29, section: "asada" },
];

const money = (value: number) => `$${value.toLocaleString("es-MX")}`;

export default function Home() {
  const [section, setSection] = useState<"flautas" | "asada">("flautas");
  const [cart, setCart] = useState<Record<string, number>>({});
  const [cartOpen, setCartOpen] = useState(false);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [pickupTime, setPickupTime] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [orderError, setOrderError] = useState("");

  const count = Object.values(cart).reduce((a, b) => a + b, 0);
  const total = useMemo(() => items.reduce((sum, item) => sum + (cart[item.id] || 0) * item.price, 0), [cart]);
  const change = (id: string, delta: number) => setCart(prev => ({ ...prev, [id]: Math.max(0, (prev[id] || 0) + delta) }));
  const order = async () => {
    setOrderError("");
    const digits = phone.replace(/\D/g, "");
    if (name.trim().length < 2 || digits.length !== 10 || !pickupTime) {
      setOrderError("Escribe tu nombre, teléfono de 10 dígitos y hora de recogida.");
      return;
    }
    setSubmitting(true);
    try {
      const response = await fetch("/api/orders", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name, phone: digits, pickupTime, notes, items: items.filter(i => cart[i.id]).map(i => ({ id: i.id, quantity: cart[i.id] })) }) });
      const result = await response.json() as { folio?: string; total?: number; error?: string };
      if (!response.ok || !result.folio) throw new Error(result.error || "No se pudo registrar el pedido.");
    const lines = items.filter(i => cart[i.id]).map(i => `• ${cart[i.id]} × ${i.name} — ${money(cart[i.id] * i.price)}`);
      const message = ["¡Hola, Beto's! Quiero confirmar este pedido para recoger:", `Folio: ${result.folio}`, `Nombre: ${name.trim()}`, `Teléfono: ${digits}`, `Hora de recogida: ${pickupTime}`, "", ...lines, "", `TOTAL: ${money(result.total ?? total)}`, "Pago: efectivo al recoger", "Lugar: Calle Oaxaca 2537", notes.trim() ? `Notas: ${notes.trim()}` : "", "", "¿Me confirman el pedido?"].filter(Boolean).join("\n");
    window.open(`https://wa.me/526561614536?text=${encodeURIComponent(message)}`, "_blank", "noopener,noreferrer");
    } catch (error) {
      setOrderError(error instanceof Error ? error.message : "No se pudo registrar el pedido.");
    } finally { setSubmitting(false); }
  };

  return (
    <main>
      <header className="hero">
        <nav><a className="brand" href="#top"><img src="/brand/betos-logo.png" alt="Beto's Flautas y Asada" /></a><a className="events-link" href="#eventos">Eventos</a></nav>
        <div className="hero-copy" id="top">
          <p className="eyebrow">Sabor casero • Fuego y tradición</p>
          <h1>Tu antojo,<br/><em>listo para recoger.</em></h1>
          <p>Elige tus favoritos, revisa el total y confirma tu pedido por WhatsApp. Pagas en efectivo al recoger.</p>
          <a className="primary" href="#menu">Ver el menú</a>
        </div>
        <div className="hero-card"><span>HOY</span><strong>Flautas</strong><small>Jue–Dom · 2–9 PM</small></div>
      </header>

      <section className="menu" id="menu">
        <div className="section-heading"><p className="eyebrow">Ordena a tu gusto</p><h2>¿Qué se te antoja?</h2></div>
        <div className="tabs" role="tablist" aria-label="Categorías del menú">
          <button className={section === "flautas" ? "active" : ""} onClick={() => setSection("flautas")}><span>JUE–DOM</span> Flautas</button>
          <button className={section === "asada" ? "active asada" : ""} onClick={() => setSection("asada")}><span>SÁB–DOM</span> Carne asada</button>
        </div>
        <div className="availability">Disponible de <strong>2:00 a 9:00 PM</strong> · Solo para recoger</div>
        <div className="products">
          {items.filter(item => item.section === section).map(item => {
            const qty = cart[item.id] || 0;
            return <article className="product" key={item.id}>
              <div><h3>{item.name}</h3>{item.description && <p>{item.description}</p>}<strong className="price">{money(item.price)}</strong></div>
              {qty ? <div className="stepper"><button aria-label={`Quitar ${item.name}`} onClick={() => change(item.id, -1)}>−</button><b>{qty}</b><button aria-label={`Agregar ${item.name}`} onClick={() => change(item.id, 1)}>+</button></div> : <button className="add" onClick={() => change(item.id, 1)}>Agregar +</button>}
            </article>;
          })}
        </div>
      </section>

      <section className="events" id="eventos">
        <div><p className="eyebrow">Beto's va a tu evento</p><h2>El sabor que reúne a todos.</h2><p>¿Cumpleaños, reunión o evento especial? Cotizamos el servicio a domicilio según tus invitados y necesidades.</p></div>
        <a className="primary light" target="_blank" rel="noreferrer" href="https://wa.me/526561614536?text=Hola%2C%20quiero%20cotizar%20un%20evento%20a%20domicilio%20con%20Beto%27s.">Cotizar mi evento</a>
      </section>

      <footer><div className="brand"><img src="/brand/betos-logo.png" alt="Beto's Flautas y Asada" /></div><p>Calle Oaxaca 2537<br/>Jueves a domingo · 2–9 PM</p><p>Pedidos: (656) 161 4536<br/>Solo para recoger</p></footer>

      {count > 0 && <button className="cart-bar" onClick={() => setCartOpen(true)}><span><b>{count}</b> Ver mi pedido</span><strong>{money(total)}</strong></button>}
      {cartOpen && <div className="overlay" onClick={() => setCartOpen(false)}><aside className="cart" onClick={e => e.stopPropagation()}>
        <div className="cart-head"><div><p className="eyebrow">Tu pedido</p><h2>Todo listo</h2></div><button onClick={() => setCartOpen(false)} aria-label="Cerrar">×</button></div>
        <div className="cart-lines">{items.filter(i => cart[i.id]).map(i => <div className="cart-line" key={i.id}><div><b>{i.name}</b><small>{money(i.price)} c/u</small></div><div className="stepper"><button onClick={() => change(i.id,-1)}>−</button><b>{cart[i.id]}</b><button onClick={() => change(i.id,1)}>+</button></div></div>)}</div>
        <div className="pickup"><span>📍</span><div><b>Recoge en Calle Oaxaca 2537</b><small>Pago en efectivo al recoger</small></div></div>
        <div className="customer-fields">
          <label>Nombre<input value={name} onChange={e => setName(e.target.value)} maxLength={80} placeholder="Tu nombre" /></label>
          <label>Teléfono<input value={phone} onChange={e => setPhone(e.target.value)} inputMode="tel" maxLength={14} placeholder="10 dígitos" /></label>
          <label>Hora para recoger<input value={pickupTime} onChange={e => setPickupTime(e.target.value)} type="time" min="14:00" max="21:00" /></label>
          <label>Notas (opcional)<textarea value={notes} onChange={e => setNotes(e.target.value)} maxLength={300} placeholder="Ej. sin salsa, bien doradas…" /></label>
        </div>
        {orderError && <p className="order-error" role="alert">{orderError}</p>}
        <div className="total"><span>Total a pagar</span><strong>{money(total)}</strong></div>
        <button className="whatsapp" onClick={order} disabled={submitting}>{submitting ? "Registrando pedido…" : "Registrar y confirmar por WhatsApp"}</button><small className="fine">Tu pedido se registra con un folio y se confirma cuando Beto's responda por WhatsApp.</small>
      </aside></div>}
    </main>
  );
}
