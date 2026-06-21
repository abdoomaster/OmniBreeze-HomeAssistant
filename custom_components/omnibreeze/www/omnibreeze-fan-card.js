class OmniBreezeFanCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("omnibreeze-fan-card-editor");
  }

  static getStubConfig(hass) {
    const states = hass?.states || {};
    const find = (domain) => Object.keys(states).find((id) => id.startsWith(`${domain}.`)) || "";

    return {
      type: "custom:omnibreeze-fan-card",
      entity: find("fan"),
      name: "OmniBreeze Fan",
      temperature: find("sensor"),
      sound: find("switch"),
      display: find("light"),
      mode: find("select"),
      countdown: find("select"),
    };
  }

  getGridOptions() {
    return {
      rows: 1,
      columns: 4,
      min_rows: 1,
      min_columns: 3,
    };
  }

  setConfig(config) {
    if (!config.entity) throw new Error("entity is required");

    this.config = {
      name: "OmniBreeze Fan",
      temperature: "",
      sound: "",
      display: "",
      mode: "",
      countdown: "",
      ...config,
    };

    this._popupOpen = false;
    this._dragging = false;
    this._local = this._local || {};
    this._lastSignature = "";
  }

  set hass(hass) {
    this._hass = hass;

    const sig = this.signature();
    if (sig === this._lastSignature && this.innerHTML && !this._forceRender) return;
    if (this._dragging) return;

    this._lastSignature = sig;
    this._forceRender = false;
    this.render();
  }

  getCardSize() {
    return 1;
  }

  getState(entityId) {
    return entityId ? this._hass?.states?.[entityId] : undefined;
  }

  fanState() {
    const fan = this.getState(this.config.entity);
    const pct = this._local.percentage ?? Number(fan?.attributes?.percentage || 0);
    const state = this._local.power ?? fan?.state ?? "off";
    const oscillating = this._local.oscillating ?? (fan?.attributes?.oscillating === true);

    return {
      raw: fan,
      state,
      isOn: state === "on",
      pct,
      oscillating,
    };
  }

  entityState(entityId, localKey) {
    if (this._local[localKey] !== undefined) return this._local[localKey];
    return this.getState(entityId)?.state;
  }

  signature() {
    if (!this._hass || !this.config) return "";

    const ids = [
      this.config.entity,
      this.config.temperature,
      this.config.sound,
      this.config.display,
      this.config.mode,
      this.config.countdown,
    ].filter(Boolean);

    return [
      this._popupOpen ? "popup" : "closed",
      JSON.stringify(this._local),
      ...ids.map((id) => {
        const st = this.getState(id);
        if (!st) return `${id}:missing`;
        return `${id}:${st.state}:${st.attributes?.percentage ?? ""}:${st.attributes?.oscillating ?? ""}`;
      }),
    ].join("|");
  }

  call(domain, service, data = {}) {
    this._hass.callService(domain, service, data);
  }

  optimisticPatch(values, ttl = 3500) {
    this._local = { ...this._local, ...values };
    this._forceRender = true;
    this.render();

    clearTimeout(this._optimisticTimer);
    this._optimisticTimer = setTimeout(() => {
      this._local = {};
      this._forceRender = true;
      this.render();
    }, ttl);
  }

  openPopup() {
    this._popupOpen = true;
    this._forceRender = true;
    this.render();
  }

  closePopup() {
    this._popupOpen = false;
    this._forceRender = true;
    this.render();
  }

  toggleFan() {
    const fan = this.fanState();
    const next = fan.isOn ? "off" : "on";

    this.optimisticPatch({ power: next });

    this.call("fan", next === "on" ? "turn_on" : "turn_off", {
      entity_id: this.config.entity,
    });
  }

  setPercentage(value) {
    const percentage = Number(value);

    this.optimisticPatch({
      power: percentage > 0 ? "on" : "off",
      percentage,
    });

    this.call("fan", "set_percentage", {
      entity_id: this.config.entity,
      percentage,
    });
  }

  toggleOscillation() {
    const fan = this.fanState();
    const next = !fan.oscillating;

    this.optimisticPatch({ oscillating: next });

    this.call("fan", "oscillate", {
      entity_id: this.config.entity,
      oscillating: next,
    });
  }

  toggleSwitch(entityId, localKey) {
    if (!entityId) return;

    const current = this.entityState(entityId, localKey);
    const next = current === "on" ? "off" : "on";

    this.optimisticPatch({ [localKey]: next });
    this.call("switch", "toggle", { entity_id: entityId });
  }

  toggleLight(entityId, localKey) {
    if (!entityId) return;

    const current = this.entityState(entityId, localKey);
    const next = current === "on" ? "off" : "on";

    this.optimisticPatch({ [localKey]: next });
    this.call("light", "toggle", { entity_id: entityId });
  }

  setSelect(entityId, option, localKey) {
    if (!entityId || !option) return;

    this.optimisticPatch({ [localKey]: option });

    this.call("select", "select_option", {
      entity_id: entityId,
      option,
    });
  }

  openMoreInfo(entityId = this.config.entity) {
    this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        bubbles: true,
        composed: true,
        detail: { entityId },
      }),
    );
  }

  renderModeButtons(entityId) {
    const st = this.getState(entityId);
    if (!st) return "";

    const current = this._local.mode ?? st.state;
    const options = st.attributes?.options || [];
    if (!options.length) return "";

    return `
      <div class="section">
        <div class="section-title">
          <ha-icon icon="mdi:tune-variant"></ha-icon>
          <span>Mode</span>
        </div>
        <div class="pill-grid">
          ${options.map((opt) => `
            <button
              class="pill ${opt === current ? "active" : ""}"
              data-select-entity="${entityId}"
              data-select-option="${opt}"
              data-select-local="mode"
            >
              ${opt}
            </button>
          `).join("")}
        </div>
      </div>
    `;
  }

  renderTimerButtons(entityId) {
    const st = this.getState(entityId);
    if (!st) return "";

    const current = this._local.countdown ?? st.state;
    const options = st.attributes?.options || [];
    if (!options.length) return "";

    return `
      <div class="section">
        <div class="section-title">
          <ha-icon icon="mdi:timer-outline"></ha-icon>
          <span>Timer</span>
        </div>
        <div class="pill-grid timer-grid">
          ${options.map((opt) => `
            <button
              class="pill ${opt === current ? "active" : ""}"
              data-select-entity="${entityId}"
              data-select-option="${opt}"
              data-select-local="countdown"
            >
              ${opt}
            </button>
          `).join("")}
        </div>
      </div>
    `;
  }

  render() {
    if (!this._hass || !this.config) return;

    const fan = this.fanState();

    if (!fan.raw) {
      this.innerHTML = `<ha-card><div style="padding:16px;">Missing fan entity: ${this.config.entity}</div></ha-card>`;
      return;
    }

    const tempSt = this.getState(this.config.temperature);
    const temp = tempSt
      ? `${tempSt.state} ${tempSt.attributes?.unit_of_measurement || ""}`.trim()
      : "—";

    const soundState = this.entityState(this.config.sound, "sound");
    const displayState = this.entityState(this.config.display, "display");
    const soundOn = soundState === "on";
    const displayOn = displayState === "on";

    const meta = temp !== "—" ? `${temp} · ${fan.pct}%` : `${fan.pct}%`;

    this.innerHTML = `
      <ha-card class="ob-card ${fan.isOn ? "on" : "off"}" data-action="open-popup">
        <div class="compact-row">
          <button class="round-icon ${fan.isOn ? "active" : ""}" data-action="toggle-fan">
            <ha-icon icon="mdi:fan"></ha-icon>
          </button>

          <div class="title">
            <div class="name">${this.config.name}</div>
            <div class="sub">${meta}</div>
          </div>
        </div>
      </ha-card>

      ${this._popupOpen ? `
        <div class="modal-backdrop" data-action="close-popup">
          <ha-card class="modal-card" data-modal-card>
            <div class="modal-header">
              <button class="close" data-action="close-popup">
                <ha-icon icon="mdi:close"></ha-icon>
              </button>

              <div class="modal-title">
                <div class="modal-name">${this.config.name}</div>
                <div class="modal-sub">${temp} · ${fan.isOn ? "On" : "Off"}</div>
              </div>

              <button class="more-info" data-action="more-info">
                <ha-icon icon="mdi:cog"></ha-icon>
              </button>
            </div>

            <div class="big-percent">${fan.pct}%</div>

            <div class="slider-shell" style="--pct:${fan.pct}%;">
              <input
                type="range"
                min="0"
                max="100"
                step="20"
                value="${fan.pct}"
                data-action="speed"
                style="--pct:${fan.pct}%;"
              />
            </div>

            <div class="main-buttons">
              <button class="${fan.isOn ? "active" : ""}" data-action="toggle-fan">
                <ha-icon icon="mdi:power"></ha-icon>
                <span>Power</span>
              </button>

              <button class="${fan.oscillating ? "active" : ""}" data-action="oscillate">
                <ha-icon icon="mdi:axis-z-rotate-clockwise"></ha-icon>
                <span>Swing</span>
              </button>

              <button class="${soundOn ? "active amber" : ""}" data-action="sound">
                <ha-icon icon="${soundOn ? "mdi:volume-high" : "mdi:volume-off"}"></ha-icon>
                <span>Sound</span>
              </button>

              <button class="${displayOn ? "active" : ""}" data-action="display">
                <ha-icon icon="${displayOn ? "mdi:monitor" : "mdi:monitor-off"}"></ha-icon>
                <span>Light</span>
              </button>
            </div>

            ${this.renderModeButtons(this.config.mode)}
            ${this.renderTimerButtons(this.config.countdown)}
          </ha-card>
        </div>
      ` : ""}

      <style>
        :host {
          display: block;
          min-width: 0;
          --ob-active: var(--state-fan-active-color, var(--state-active-color, var(--primary-color)));
          --ob-card-bg: var(--ha-card-background, var(--card-background-color));
          --ob-muted-bg: color-mix(in srgb, var(--primary-text-color) 9%, transparent);
          --ob-muted-bg-2: color-mix(in srgb, var(--primary-text-color) 14%, transparent);
          --ob-border: color-mix(in srgb, var(--primary-text-color) 13%, transparent);
          --ob-shadow: var(--ha-card-box-shadow, 0 12px 26px rgba(0,0,0,.22));
        }

        .ob-card {
          box-sizing: border-box;
          width: 100%;
          min-width: 0;
          border-radius: var(--ha-card-border-radius, 24px);
          padding: 12px 14px;
          background:
            linear-gradient(
              135deg,
              color-mix(in srgb, var(--ob-active) 9%, var(--ob-card-bg)) 0%,
              var(--ob-card-bg) 72%
            );
          border: 1px solid var(--ob-border);
          box-shadow: var(--ob-shadow);
          color: var(--primary-text-color);
          overflow: hidden;
          cursor: pointer;
        }

        .ob-card.off {
          background:
            linear-gradient(
              135deg,
              color-mix(in srgb, var(--primary-text-color) 5%, var(--ob-card-bg)) 0%,
              var(--ob-card-bg) 72%
            );
        }

        .compact-row {
          display: grid;
          grid-template-columns: 48px minmax(0, 1fr);
          align-items: center;
          gap: 12px;
          min-width: 0;
        }

        .round-icon {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          border: 0;
          background: var(--ob-muted-bg);
          color: var(--secondary-text-color);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          padding: 0;
        }

        .round-icon.active {
          color: var(--ob-active);
          background: color-mix(in srgb, var(--ob-active) 18%, transparent);
        }

        .round-icon ha-icon {
          width: 28px;
          height: 28px;
        }

        .title {
          min-width: 0;
          overflow: hidden;
        }

        .name {
          font-size: 18px;
          line-height: 1.1;
          font-weight: 800;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .sub {
          margin-top: 4px;
          font-size: 13px;
          line-height: 1.2;
          color: var(--secondary-text-color);
          font-weight: 700;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .modal-backdrop {
          position: fixed;
          inset: 0;
          z-index: 999;
          background: rgba(0, 0, 0, 0.55);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 18px;
          box-sizing: border-box;
        }

        .modal-card {
          width: min(560px, 94vw);
          max-height: min(820px, 92vh);
          overflow: auto;
          border-radius: 28px;
          padding: 18px;
          background: var(--ob-card-bg);
          border: 1px solid var(--ob-border);
          box-shadow: 0 22px 60px rgba(0,0,0,.45);
          color: var(--primary-text-color);
        }

        .modal-header {
          display: grid;
          grid-template-columns: 44px minmax(0, 1fr) 44px;
          align-items: center;
          gap: 10px;
          margin-bottom: 18px;
        }

        .close,
        .more-info {
          width: 44px;
          height: 44px;
          border-radius: 50%;
          border: 0;
          background: var(--ob-muted-bg);
          color: var(--primary-text-color);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }

        .modal-title {
          min-width: 0;
          text-align: center;
        }

        .modal-name {
          font-size: 22px;
          font-weight: 850;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .modal-sub {
          margin-top: 4px;
          color: var(--secondary-text-color);
          font-size: 14px;
          font-weight: 700;
        }

        .big-percent {
          text-align: center;
          font-size: 54px;
          font-weight: 700;
          line-height: 1;
          margin-bottom: 18px;
        }

        .slider-shell {
          height: 54px;
          border-radius: 20px;
          background:
            linear-gradient(
              90deg,
              var(--ob-active) 0%,
              var(--ob-active) var(--pct),
              var(--ob-muted-bg-2) var(--pct),
              var(--ob-muted-bg-2) 100%
            );
          border: 1px solid var(--ob-border);
          display: flex;
          align-items: center;
          padding: 0 14px;
          margin-bottom: 12px;
          box-shadow: inset 0 1px 0 color-mix(in srgb, white 8%, transparent);
        }

        input[type="range"] {
          -webkit-appearance: none;
          appearance: none;
          width: 100%;
          height: 36px;
          background: transparent;
          cursor: pointer;
          margin: 0;
        }

        input[type="range"]::-webkit-slider-runnable-track {
          height: 36px;
          background: transparent;
          border-radius: 999px;
        }

        input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 8px;
          height: 28px;
          border-radius: 999px;
          background: var(--primary-text-color);
          border: 0;
          margin-top: 4px;
          box-shadow: 0 1px 5px rgba(0,0,0,.32);
        }

        input[type="range"]::-moz-range-track {
          height: 36px;
          background: transparent;
          border-radius: 999px;
        }

        input[type="range"]::-moz-range-thumb {
          width: 8px;
          height: 28px;
          border-radius: 999px;
          background: var(--primary-text-color);
          border: 0;
          box-shadow: 0 1px 5px rgba(0,0,0,.32);
        }

        .main-buttons {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 8px;
          margin-bottom: 12px;
        }

        .main-buttons button,
        .pill {
          border: 0;
          border-radius: 18px;
          background: var(--ob-muted-bg);
          color: var(--primary-text-color);
          cursor: pointer;
          font: inherit;
          min-width: 0;
        }

        .main-buttons button {
          min-height: 64px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 5px;
        }

        .main-buttons button.active,
        .pill.active {
          background: var(--ob-active);
          color: var(--text-primary-color, white);
        }

        .main-buttons button.amber {
          background: var(--warning-color, #f5b942);
          color: var(--text-primary-color, white);
        }

        .main-buttons ha-icon {
          width: 26px;
          height: 26px;
        }

        .main-buttons span {
          font-size: 12px;
          font-weight: 800;
          white-space: nowrap;
        }

        .section {
          margin-top: 8px;
          border-radius: 18px;
          background: var(--ob-muted-bg);
          border: 1px solid var(--ob-border);
          padding: 10px;
        }

        .section-title {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 8px;
          font-size: 13px;
          font-weight: 850;
        }

        .section-title ha-icon {
          width: 18px;
          height: 18px;
          color: var(--ob-active);
        }

        .pill-grid {
          display: flex;
          flex-wrap: wrap;
          gap: 7px;
        }

        .pill {
          min-height: 36px;
          padding: 0 13px;
          font-size: 12px;
          font-weight: 800;
        }

        .timer-grid {
          max-height: 120px;
          overflow-y: auto;
        }

        @media (max-width: 700px) {
          .main-buttons {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }
      </style>
    `;

    this.querySelectorAll("[data-action]").forEach((el) => {
      el.onclick = (ev) => {
        ev.stopPropagation();
        const action = el.dataset.action;

        if (action === "open-popup") this.openPopup();
        if (action === "close-popup") this.closePopup();
        if (action === "toggle-fan") this.toggleFan();
        if (action === "oscillate") this.toggleOscillation();
        if (action === "sound") this.toggleSwitch(this.config.sound, "sound");
        if (action === "display") this.toggleLight(this.config.display, "display");
        if (action === "more-info") this.openMoreInfo();
      };
    });

    const modalCard = this.querySelector("[data-modal-card]");
    if (modalCard) {
      modalCard.onclick = (ev) => ev.stopPropagation();
    }

    const slider = this.querySelector('[data-action="speed"]');

    if (slider) {
      const setVisual = () => {
        const pct = Number(slider.value || 0);
        slider.style.setProperty("--pct", `${pct}%`);
        slider.closest(".slider-shell")?.style.setProperty("--pct", `${pct}%`);
        const percent = this.querySelector(".big-percent");
        if (percent) percent.textContent = `${pct}%`;
      };

      slider.oninput = () => {
        this._dragging = true;
        setVisual();
      };

      slider.onchange = (ev) => {
        this._dragging = false;
        setVisual();
        this.setPercentage(ev.target.value);
      };

      slider.onpointerup = () => {
        this._dragging = false;
      };
    }

    this.querySelectorAll("[data-select-entity]").forEach((btn) => {
      btn.onclick = (ev) => {
        ev.stopPropagation();
        this.setSelect(
          btn.dataset.selectEntity,
          btn.dataset.selectOption,
          btn.dataset.selectLocal,
        );
      };
    });
  }
}

class OmniBreezeFanCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...(config || {}) };
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  fireConfigChanged(config) {
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        bubbles: true,
        composed: true,
        detail: { config },
      }),
    );
  }

  updateConfig(key, value) {
    const next = { ...(this._config || {}) };

    if (value === "" || value === undefined || value === null) {
      delete next[key];
    } else {
      next[key] = value;
    }

    if (!next.type) next.type = "custom:omnibreeze-fan-card";

    this._config = next;
    this.fireConfigChanged(next);
  }

  renderEntityPicker(label, key, domain) {
    const value = this._config?.[key] || "";

    return `
      <label class="field">
        <span>${label}</span>
        <ha-entity-picker
          domain="${domain}"
          data-key="${key}"
          value="${value}"
          allow-custom-entity
        ></ha-entity-picker>
      </label>
    `;
  }

  render() {
    if (!this._config) return;

    this.innerHTML = `
      <div class="editor">
        <label class="field">
          <span>Name</span>
          <input data-key="name" value="${this._config.name || ""}" placeholder="Kitchen Fan" />
        </label>

        ${this.renderEntityPicker("Fan entity", "entity", "fan")}
        ${this.renderEntityPicker("Temperature sensor", "temperature", "sensor")}
        ${this.renderEntityPicker("Sound switch", "sound", "switch")}
        ${this.renderEntityPicker("Display light", "display", "light")}
        ${this.renderEntityPicker("Mode select", "mode", "select")}
        ${this.renderEntityPicker("Timer select", "countdown", "select")}
      </div>

      <style>
        .editor {
          display: grid;
          gap: 14px;
          padding: 8px 0;
        }

        .field {
          display: grid;
          gap: 6px;
        }

        .field span {
          font-size: 13px;
          font-weight: 700;
          color: var(--primary-text-color);
        }

        input {
          min-height: 40px;
          border-radius: 10px;
          border: 1px solid var(--divider-color);
          background: var(--card-background-color);
          color: var(--primary-text-color);
          padding: 0 12px;
          font: inherit;
        }
      </style>
    `;

    this.querySelectorAll("ha-entity-picker").forEach((picker) => {
      picker.hass = this._hass;
      picker.addEventListener("value-changed", (ev) => {
        this.updateConfig(picker.dataset.key, ev.detail.value);
      });
    });

    this.querySelectorAll("input").forEach((input) => {
      input.addEventListener("change", () => {
        this.updateConfig(input.dataset.key, input.value);
      });
    });
  }
}

if (!customElements.get("omnibreeze-fan-card")) {
  customElements.define("omnibreeze-fan-card", OmniBreezeFanCard);
}

if (!customElements.get("omnibreeze-fan-card-editor")) {
  customElements.define("omnibreeze-fan-card-editor", OmniBreezeFanCardEditor);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "omnibreeze-fan-card",
  name: "OmniBreeze Fan Card",
  description: "Compact OmniBreeze fan card with popup controls.",
});
