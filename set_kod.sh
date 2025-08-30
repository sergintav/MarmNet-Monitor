#!/bin/bash

# MarmNet Monitor Kurulum Script'i
# Yazan: Semih Ergintav
# Bu script virtual environment oluşturur ve gerekli paketleri yükler

echo "========================================="
echo "MarmNet Monitor Kurulum Script'i"
echo "========================================="

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Python versiyonunu kontrol et
echo -e "${BLUE}Python versiyonu kontrol ediliyor...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}HATA: Python3 bulunamadı. Lütfen Python3'ü yükleyin.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Python versiyonu: $PYTHON_VERSION${NC}"

# Virtual environment dizin adı
VENV_DIR="marmnet_env"

# Eğer virtual environment varsa sor
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment '$VENV_DIR' zaten mevcut.${NC}"
    read -p "Mevcut environment'ı silip yeniden oluşturulsun mu? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Mevcut virtual environment siliniyor...${NC}"
        rm -rf "$VENV_DIR"
    else
        echo -e "${YELLOW}Mevcut environment kullanılacak.${NC}"
    fi
fi

# Virtual environment oluştur
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}Virtual environment oluşturuluyor...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}HATA: Virtual environment oluşturulamadı.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment başarıyla oluşturuldu.${NC}"
fi

# Virtual environment'ı aktif et
echo -e "${BLUE}Virtual environment aktif ediliyor...${NC}"
source "$VENV_DIR/bin/activate"

# pip'i güncelle
echo -e "${BLUE}pip güncelleniyor...${NC}"
pip install --upgrade pip

# Gerekli paketleri yükle
echo -e "${BLUE}Gerekli paketler yükleniyor...${NC}"
pip install flask 

# Kurulum kontrolü
echo -e "${BLUE}Kurulum kontrol ediliyor...${NC}"
python3 -c "
try:
    import flask
    print('✓ Flask başarıyla yüklendi')
    print(f'  Versiyon: {flask.__version__}')
except ImportError as e:
    print(f'✗ Paket yüklenemedi: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}Kurulum başarısız!${NC}"
    exit 1
fi

# stations.txt örnek dosyası oluştur
if [ ! -f "stations.txt" ]; then
    echo -e "${BLUE}Örnek stations.txt dosyası oluşturuluyor...${NC}"
    cat > stations.txt << 'EOF'
# MarmNet Monitor İstasyon Dosyası
# Format: İstasyon_Adı IP_Adresi Enlem Boylam
# Örnek veriler:
Istanbul 8.8.8.8 41.0082 28.9784
Ankara 8.8.4.4 39.9334 32.8597
Izmir 1.1.1.1 38.4192 27.1287
EOF
    echo -e "${GREEN}Örnek stations.txt dosyası oluşturuldu.${NC}"
else
    echo -e "${YELLOW}stations.txt dosyası zaten mevcut.${NC}"
fi

# Çalıştırma script'i oluştur
cat > run_marmnet.sh << 'EOF'
#!/bin/bash
# MarmNet Monitor Çalıştırma Script'i

# Virtual environment'ı aktif et
source marmnet_env/bin/activate

# Uygulamayı çalıştır
echo "MarmNet Monitor başlatılıyor..."
echo "Tarayıcınızda http://localhost:50001 adresini açın"
python3 app.py "$@"
EOF

chmod +x run_marmnet.sh

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Kurulum tamamlandı!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${BLUE}Kullanım:${NC}"
echo -e "1. ${YELLOW}./run_marmnet.sh${NC}                    # Varsayılan ayarlarla çalıştır"
echo -e "2. ${YELLOW}./run_marmnet.sh --port 8080${NC}        # Farklı port"
echo -e "3. ${YELLOW}./run_marmnet.sh --interval 60${NC}      # 60 saniye yenileme"
echo -e "4. ${YELLOW}./run_marmnet.sh --stations my.txt${NC}  # Farklı istasyon dosyası"
echo ""
echo -e "${BLUE}Manuel çalıştırma:${NC}"
echo -e "1. ${YELLOW}source marmnet_env/bin/activate${NC}     # Virtual environment aktif et"
echo -e "2. ${YELLOW}python3 app.py${NC}                     # Uygulamayı çalıştır"
echo ""
echo -e "${BLUE}Dosyalar:${NC}"
echo -e "• ${YELLOW}app.py${NC}           - Ana uygulama"
echo -e "• ${YELLOW}stations.txt${NC}     - İstasyon bilgileri"
echo -e "• ${YELLOW}run_marmnet.sh${NC}   - Çalıştırma script'i"
echo -e "• ${YELLOW}marmnet_env/${NC}     - Virtual environment"
echo ""
echo -e "${GREEN}Kurulum başarıyla tamamlandı!${NC}"
