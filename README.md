# 🌍 KNMI Seismische Activiteit voor Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/DonTranQuiL/knmi_seismisch/releases)
[![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/DonTranQuiL/knmi_seismisch/commits/main)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.5+-blue.svg)](https://www.home-assistant.io/)

Een efficiënte en robuuste Home Assistant integratie die de meest recente seismische activiteit (aardbevingen, geïnduceerde bevingen en gecontroleerde explosies) in Nederland en de overzeese gebieden ophaalt via de officiële KNMI API.

## ✨ Functionaliteiten

* **Smart Cache Booting:** Laadt data na een herstart direct in vanaf de lokale schijf. Home Assistant hoeft niet te wachten op internet, wat zorgt voor een bliksemsnelle opstarttijd.
* **Achtergrond Verwerking:** Zware XML-parsing en netwerkverzoeken worden op de achtergrond (`executor_job`) uitgevoerd, waardoor je systeem niet blokkeert of vertraagt.
* **Uitgebreide Data:** Haalt locatie, regio, magnitude, diepte, datum/tijd en het **type beving** (bijv. Natuurlijk of Geïnduceerd door gaswinning) op.
* **Meertalig:** Volledige ondersteuning voor Nederlands en Engels (zowel de UI als de sensor-namen).
* **Zoekfilters:** Filter bevingen op basis van specifieke zoektermen (bijv. alleen "Groningen" of "Limburg").

## 📥 Installatie via HACS

1. Ga in Home Assistant naar **HACS** > **Integraties**.
2. Klik rechtsboven op de drie puntjes en kies **Aangepaste repositories** (Custom repositories).
3. Voeg de URL van deze repository toe en kies als categorie **Integratie**.
4. Klik op toevoegen, zoek naar *KNMI Seismische Activiteit* in HACS en klik op **Download**.
5. Herstart Home Assistant.

## ⚙️ Configuratie

1. Ga naar **Instellingen** > **Apparaten & Diensten**.
2. Klik rechtsonder op **+ Integratie toevoegen**.
3. Zoek naar **KNMI Seismisch**.
4. Vul een naam in (bijv. "Nederland") en laat "Zoektermen" leeg als je alle bevingen wilt zien.

## 📊 Dashboard Kaart (Markdown)

Gebruik deze code in een Markdown-kaart voor een prachtig, dynamisch overzicht dat van kleur verandert op basis van de kracht van de beving.

```yaml
type: markdown
content: >-
  {% set entity = 'sensor.knmi_seismisch_nederland_earthquakes' %} {% if
  states(entity) in ['unknown', 'unavailable'] %} {% set entity =
  'sensor.knmi_seismisch_nederland_aardbevingen_nederland' %} {% endif %} {% set
  mag = states(entity) | float(0) %}

  ## 🌍 KNMI Seismische Activiteit

  {% if states(entity) not in ['unknown', 'unavailable', 'Geen bevingen'] %} {%
  set color = '#00C853' %} {% if mag >= 2.0 %}{% set color = '#FF9800' %}{%
  endif %} {% if mag >= 3.0 %}{% set color = '#F44336' %}{% endif %}

  <div style="background-color: rgba(128, 128, 128, 0.1); padding: 15px;
  border-radius: 10px; border-left: 6px solid {{ color }};"> <h3
  style="margin-top: 0; padding-top: 0;">Meest Recente Beving</h3> <div
  style="display: flex; align-items: center; gap: 15px;"> <div style="font-size:
  32px; font-weight: bold; color: {{ color }};">{{ mag }}</div> <div
  style="line-height: 1.4;"> 📍 <b>{{ state_attr(entity, 'location') }}</b>  {%
  if state_attr(entity, 'region') != 'Not specified' %} <span style="opacity:
  0.7; font-size: 0.9em;">({{ state_attr(entity, 'region') }})</span> {% endif
  %}<br> 🕒 {{ state_attr(entity, 'time') }}<br> 📏 Diepte: {{
  state_attr(entity, 'depth_km') }} km | ⚠️ {{ state_attr(entity, 'event_type')
  }} </div> </div> </div> <br>

  📜 Eerdere Bevingen <table style="width: 100%; text-align: left;
  border-collapse: collapse; font-size: 0.85em;"> <tr> <th style="border-bottom:
  1px solid rgba(128, 128, 128, 0.3); padding: 8px 0;">Mag</th> <th
  style="border-bottom: 1px solid rgba(128, 128, 128, 0.3); padding: 8px
  0;">Locatie</th> <th style="border-bottom: 1px solid rgba(128, 128, 128, 0.3);
  padding: 8px 0;">Diepte</th> <th style="border-bottom: 1px solid rgba(128,
  128, 128, 0.3); padding: 8px 0;">Type</th> <th style="border-bottom: 1px solid
  rgba(128, 128, 128, 0.3); padding: 8px 0;">Datum</th> </tr> {% if
  state_attr(entity, 'history') %} {% for item in state_attr(entity,
  'history')[:7] %} <tr> <td style="padding: 8px 0; font-weight: bold; color: {%
  if item.magnitude | float(0) >= 3.0 %}#F44336{% elif item.magnitude | float(0)
  >= 2.0 %}#FF9800{% else %}#00C853{% endif %};">{{ item.magnitude }}</td> <td
  style="padding: 8px 0;">{{ item.city }}</td> <td style="padding: 8px 0;">{{
  item.depth_km }}km</td> <td style="padding: 8px 0; opacity: 0.9; font-size:
  0.9em;"><i>{{ item.event_type }}</i></td> <td style="padding: 8px 0; opacity:
  0.7;">{{ item.time.split(' ')[0] }}</td> </tr> {% endfor %} {% endif %}
  </table>

  {% else %}

  ✅ Er is momenteel geen recente seismische activiteit gemeld door het KNMI.

  {% endif %}


  ```
<img width="490" height="650" alt="{6AAD05F9-B18C-4ED3-B586-7479398FD3FF}" src="https://github.com/user-attachments/assets/e30aa5f1-96c4-495f-acdc-112d28ce309a" />

[hacs]: https://hacs.xyz
[hacs_badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[maintenance_badge]: https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge

  
