# AFIP ml-service (data halisi pekee)

## Unachohitaji kuweka (siwezi kukutengenezea)
1. data/raw/nbs/yield_labels.csv  - mavuno HALISI ya mahindi (angalia yield_labels.TEMPLATE.csv)
   Safu: plot_id,region,latitude,longitude,year,yield_t_ha,source,collection_date
   Vyanzo: NBS Tanzania, World Bank LSMS-ISA (Tanzania National Panel Survey), data ya Wizara/utafiti.
   Chini ya safu 200 na mikoa 6 validation itakataa.
2. data/raw/sentinel2/ndvi.csv    - plot_id,year,ndvi_max (NDVI ya juu ya msimu kutoka Sentinel-2)
3. Faili ya chanzo/leseni kwenye data/external_metadata/

## Hatua
python -m venv .venv ; .venv\Scripts\activate ; pip install -r requirements.txt
python preprocessing\build_dataset.py --season-start-month 11 --season-end-month 5
python validation\validate_dataset.py
python train_model.py
uvicorn main:app --port 8000
Kisha jaribu: http://localhost:8000/health na /docs