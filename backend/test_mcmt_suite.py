import requests

base = 'http://127.0.0.1:8000'

# 1. Test Static Files
r_html = requests.get(f'{base}/cipher.html')
assert r_html.status_code == 200, f'cipher.html returned {r_html.status_code}'
assert 'mcmt-mode-selector' in r_html.text, 'mcmt-mode-selector missing in cipher.html'
print('[PASS] cipher.html verified (contains mcmt-mode-selector)')

r_js = requests.get(f'{base}/app.js')
assert r_js.status_code == 200, f'app.js returned {r_js.status_code}'
assert 'initRouteSearchModule' in r_js.text, 'initRouteSearchModule missing in app.js'
assert 'plotRouteOnGIS' in r_js.text, 'plotRouteOnGIS missing in app.js'
print('[PASS] app.js verified (contains initRouteSearchModule and plotRouteOnGIS)')

r_css = requests.get(f'{base}/styles.css')
assert r_css.status_code == 200, f'styles.css returned {r_css.status_code}'
assert 'timeline-node-card' in r_css.text, 'timeline-node-card missing in styles.css'
print('[PASS] styles.css verified (contains timeline-node-card)')

# 2. Test Cameras Registry API
r_cams = requests.get(f'{base}/api/tracking/cameras')
assert r_cams.status_code == 200
cams_data = r_cams.json()
assert cams_data['totalCameras'] >= 30
print(f"[PASS] /api/tracking/cameras verified: {cams_data['totalCameras']} camera nodes online")

# 3. Test Plate Route Reconstruction
r_route = requests.post(f'{base}/api/tracking/reconstruct-route', json={'plate': 'GJ01YH7564'})
assert r_route.status_code == 200
route_data = r_route.json()
assert len(route_data['timeline']) == 5
assert route_data['isKinematicallyFeasible'] is True
assert route_data['totalDistanceKm'] > 20
print(f"[PASS] /api/tracking/reconstruct-route verified for GJ01YH7564: {len(route_data['timeline'])} nodes, {route_data['totalDistanceKm']} km, Feasible={route_data['isKinematicallyFeasible']}")

# 4. Test Vehicle Appearance Search
r_v = requests.post(f'{base}/api/tracking/search', json={'vehicleQuery': {'vehicleClass': '2-Wheeler', 'vehicleColor': 'Black', 'make': 'Apache'}})
assert r_v.status_code == 200
v_data = r_v.json()
assert len(v_data['timeline']) >= 1
print(f"[PASS] /api/tracking/search (Vehicle Appearance) verified: {len(v_data['timeline'])} transit nodes matched")

# 5. Test Person Re-ID Search
r_p = requests.post(f'{base}/api/tracking/search', json={'personQuery': {'gender': 'Male', 'upperColor': 'Black', 'lowerColor': 'Blue'}})
assert r_p.status_code == 200
p_data = r_p.json()
assert len(p_data['timeline']) >= 1
print(f"[PASS] /api/tracking/search (Person Re-ID) verified: {len(p_data['timeline'])} transit nodes matched")

print("\nALL VERIFICATION TESTS COMPLETED WITH 100% SUCCESS!")
