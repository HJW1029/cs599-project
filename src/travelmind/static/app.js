const categoryNames = {
  scenic: "景点",
  food: "美食",
  culture: "文化",
  shopping: "购物",
  leisure: "休闲",
};

let selectedLocation = { lat: 30.2741, lng: 120.1551, label: "杭州" };
let selectedMarker = null;
let poiLayer = null;
let recommendationMarkers = [];

const map = L.map("map").setView([selectedLocation.lat, selectedLocation.lng], 13);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

poiLayer = L.layerGroup().addTo(map);

function setSelectedMarker(location) {
  const icon = L.divIcon({
    className: "",
    html: '<span class="selected-marker">选</span>',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -16],
  });
  if (selectedMarker) {
    selectedMarker.setLatLng([location.lat, location.lng]);
  } else {
    selectedMarker = L.marker([location.lat, location.lng], { draggable: true, icon }).addTo(map);
    selectedMarker.on("dragend", () => {
      const next = selectedMarker.getLatLng();
      selectedLocation = { lat: next.lat, lng: next.lng, label: "地图拖拽位置" };
      updateStatus();
    });
  }
  selectedMarker.bindPopup("已选择位置").openPopup();
}

function setSelectedLocation(location, zoom = 15) {
  selectedLocation = location;
  setSelectedMarker(location);
  map.setView([location.lat, location.lng], zoom);
  updateStatus(location.label || undefined);
}

setSelectedMarker(selectedLocation);

map.on("click", (event) => {
  selectedLocation = {
    lat: event.latlng.lat,
    lng: event.latlng.lng,
    label: "地图选点",
  };
  setSelectedMarker(selectedLocation);
  updateStatus();
});

const radius = document.querySelector("#radius");
const radiusValue = document.querySelector("#radiusValue");
const statusEl = document.querySelector("#status");
const recommendBtn = document.querySelector("#recommendBtn");
const searchInput = document.querySelector("#searchInput");
const searchBtn = document.querySelector("#searchBtn");
const locateBtn = document.querySelector("#locateBtn");
const searchResults = document.querySelector("#searchResults");

radius.addEventListener("input", () => {
  radiusValue.textContent = `${Number(radius.value).toFixed(1)}km`;
});

recommendBtn.addEventListener("click", recommend);
searchBtn.addEventListener("click", searchPlace);
locateBtn.addEventListener("click", locateUser);
searchInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    searchPlace();
  }
});

function updateStatus(text) {
  if (text) {
    statusEl.textContent = text;
    return;
  }
  statusEl.textContent = `${selectedLocation.lat.toFixed(4)}, ${selectedLocation.lng.toFixed(4)}`;
}

function readPreferences() {
  const categories = [...document.querySelectorAll(".chips input:checked")].map((input) => input.value);
  return {
    categories: categories.length ? categories : ["scenic", "culture", "food"],
    max_distance_km: Number(radius.value),
    pace: document.querySelector("#pace").value,
  };
}

async function recommend() {
  updateStatus("Agent 运行中");
  recommendBtn.disabled = true;
  const payload = {
    location: selectedLocation,
    preferences: readPreferences(),
    limit: 8,
  };

  try {
    const response = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    renderResults(data);
    if (data.recommendations.length === 0) {
      updateStatus("没有真实推荐结果");
    } else {
      updateStatus(data.used_fallback_data ? "未连接到实时地图数据" : "推荐完成");
    }
  } catch (error) {
    updateStatus("推荐失败");
    document.querySelector("#recommendations").innerHTML = `<div class="card">请求失败：${error.message}</div>`;
  } finally {
    recommendBtn.disabled = false;
  }
}

async function searchPlace() {
  const q = searchInput.value.trim();
  if (!q) {
    searchResults.innerHTML = "";
    return;
  }
  searchBtn.disabled = true;
  updateStatus("搜索中");
  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=5`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const results = await response.json();
    renderSearchResults(results);
    updateStatus(results.length ? "选择搜索结果" : "没有搜索结果");
  } catch (error) {
    searchResults.innerHTML = `<button type="button" class="search-result">搜索失败：${escapeHtml(error.message)}</button>`;
    updateStatus("搜索失败");
  } finally {
    searchBtn.disabled = false;
  }
}

function renderSearchResults(results) {
  if (!results.length) {
    searchResults.innerHTML = '<button type="button" class="search-result">没有找到相关地点</button>';
    return;
  }
  searchResults.innerHTML = results
    .map(
      (item, index) =>
        `<button type="button" class="search-result" data-search-index="${index}">${escapeHtml(shortLabel(item.label))}</button>`,
    )
    .join("");
  [...searchResults.querySelectorAll("[data-search-index]")].forEach((button) => {
    button.addEventListener("click", () => {
      const item = results[Number(button.dataset.searchIndex)];
      setSelectedLocation({ lat: item.lat, lng: item.lng, label: shortLabel(item.label) }, 15);
      searchResults.innerHTML = "";
    });
  });
}

function locateUser() {
  if (!navigator.geolocation) {
    updateStatus("浏览器不支持定位");
    return;
  }
  locateBtn.disabled = true;
  updateStatus("定位中");
  navigator.geolocation.getCurrentPosition(
    (position) => {
      setSelectedLocation(
        {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          label: "当前位置",
        },
        15,
      );
      locateBtn.disabled = false;
    },
    () => {
      updateStatus("定位失败或未授权");
      locateBtn.disabled = false;
    },
    { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 },
  );
}

function renderResults(data) {
  document.querySelector("#countMetric").textContent = data.recommendations.length;
  document.querySelector("#traceMetric").textContent = data.trace_id.slice(0, 8);

  const cards = document.querySelector("#recommendations");
  cards.classList.remove("empty");
  poiLayer.clearLayers();
  recommendationMarkers = [];
  if (!data.recommendations.length) {
    cards.classList.add("empty");
    cards.innerHTML = "附近没有查到符合当前偏好的真实地图地点。可以扩大搜索半径，或切换为景点、文化、美食等其他类型。";
    document.querySelector("#itinerary").innerHTML = "";
    return;
  }
  cards.innerHTML = data.recommendations
    .map((item, index) => {
      const poi = item.poi;
      return `
        <article class="card" data-poi-index="${index}">
          <div class="card-head">
            <div class="rank-title">
              <span class="rank-badge">${index + 1}</span>
              <h3>${escapeHtml(poi.name)}</h3>
            </div>
            <span class="tag">${categoryNames[poi.category] || poi.category}</span>
          </div>
          <p class="reason">${escapeHtml(item.reason)}</p>
          <div class="meta">
            <span>直线 ${formatDistance(poi.distance_km)}</span>
            <span>${poi.rating.toFixed(1)}分</span>
            <span>推荐分 ${item.score.toFixed(2)}</span>
            <span>${item.suggested_duration_minutes}分钟</span>
          </div>
        </article>
      `;
    })
    .join("");
  [...cards.querySelectorAll("[data-poi-index]")].forEach((card) => {
    card.addEventListener("click", () => {
      focusRecommendation(Number(card.dataset.poiIndex));
    });
  });

  const timeline = document.querySelector("#itinerary");
  timeline.innerHTML = data.itinerary
    .map(
      (stop) =>
        `<li><strong>${stop.order}. ${escapeHtml(stop.name)}</strong><br /><span class="reason">${categoryNames[stop.category]} · 直线 ${formatDistance(stop.distance_km)} · ${stop.suggested_duration_minutes}分钟</span></li>`,
    )
    .join("");

  const bounds = [];
  data.recommendations.forEach((item, index) => {
    const poi = item.poi;
    const marker = L.marker([poi.lat, poi.lng], {
      icon: L.divIcon({
        className: "",
        html: `<span class="poi-marker">${index + 1}</span>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -14],
      }),
    })
      .bindPopup(`<strong>${escapeHtml(poi.name)}</strong><br />直线 ${formatDistance(poi.distance_km)} · ${poi.rating.toFixed(1)}分`)
      .bindTooltip(`${index + 1}. ${escapeHtml(poi.name)}`, {
        permanent: true,
        direction: "right",
        className: "poi-label",
        offset: [12, 0],
      })
      .addTo(poiLayer);
    recommendationMarkers.push(marker);
    bounds.push([poi.lat, poi.lng]);
  });
  if (bounds.length) {
    bounds.push([data.center.lat, data.center.lng]);
    map.fitBounds(bounds, { padding: [36, 36], maxZoom: 16 });
  }
}

function focusRecommendation(index) {
  const marker = recommendationMarkers[index];
  if (!marker) {
    return;
  }
  map.setView(marker.getLatLng(), Math.max(map.getZoom(), 16));
  marker.openPopup();
}

function shortLabel(label) {
  return String(label).split(",").slice(0, 3).join(", ");
}

function formatDistance(distanceKm) {
  if (distanceKm < 1) {
    return `${Math.round(distanceKm * 1000)}m`;
  }
  return `${distanceKm.toFixed(2)}km`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

updateStatus();
