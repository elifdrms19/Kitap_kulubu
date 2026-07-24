from pyngrok import ngrok

# Kendi kopyaladığın Authtoken'ı tırnak içine yapıştır
ngrok.set_auth_token("3GroBJkCXub0Fv7Zv1FbzgbjAT9_3Xpu94V7mdaMzuzkJCoXc")

# Tüneli başlat
public_url = ngrok.connect(8501)
print("\n🔗 Telefon adresi:", public_url)