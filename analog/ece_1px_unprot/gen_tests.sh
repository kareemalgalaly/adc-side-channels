# Build seeds

corners=( tt ss ff sf fs )

python ../../script/template_engine.py ece_1px_unprot.temp.cir -s halfcounter= plot= -o demo_unprot.cir
python ../../script/template_engine.py ece_1px_unprot.temp.cir -s halfcounter= plot= protected= -o demo_prot.cir

for corner in ${corners[@]}; do
    python ../../script/template_engine.py ece_1px_unprot.temp.cir -s halfcounter= "randvec_0=eval:'compose randvec_0 '+' '.join(str(i) for i in range(256))" -o runme_${corner}_unprot.cir
    python ../../script/template_engine.py ece_1px_unprot.temp.cir -s halfcounter= "randvec_0=eval:'compose randvec_0 '+' '.join(str(i) for i in range(256))" protected= -o runme_${corner}_prot.cir
done

