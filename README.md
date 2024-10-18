# SingleSlopeADC_Mixed

# Tools Required
- ngspice
- verilog
- verilator
- x-server (XQuartz on Mac)

# How to run
## Analog
```
cd analog
ngspice vlnggen -- --CFLAGS -DVL_TIME_STAMP64 --CFLAGS -DVL_NO_LEGACY adc.v
ngspice adc.cir
```

# Additional Documentation
https://ngspice.sourceforge.io/docs/ngspice-manual.pdf

## Spice Quickstart
```
Quick Reference
  Basic Devices                                                                                                                                                                                                                                                                      
    resistor      : rname N1 N2 Resistance                                                                                                                                                                                                                                           
    capacitor     : cname N1 N2 Resistance [IC=valueV]                                                                                                                                                                                                                               
    inductor      : lname N1 N2 Inductance [IC=valueA]                                                                                                                                                                                                                               
                                                                                                                                                                                                                                                                                     
  Sources                                                            
    voltage       : vname N1 N2 ((DC|AC|TRAN) Voltage|FUNCTION)                                                                           
    current       : iname N1 N2 ((DC|AC|TRAN) Current|FUNCTION)                                                                           

      SIN(VO VA FREQ [TD] [THETA] [PHASE])                           
          VO = offset voltage     VA = amplitude voltage            FREQ = frequency hz                                                   
          TD = delay in seconds   THETA = damping factor / second   PHASE = phase in degress                                              

      PULSE(V1 V2 TD Tr Tf PW Period [NPer])                         
          V1 = initial voltage    V2 = peak voltage   TD = initial delay   Tr = Rise time                                                 
          Tf = fall time          PW = pulse-width    Period = period      NPer = number of periods                                       

      PWL(T1 V1 T2 V2 ...)                                           
      ...                                                            

    vctrl voltage : ename N1 N2 NC1 NC2 Voltage                      
    vctrl current : gname N1 N2 NC1 NC2 Voltage                      
      NC1 NC2 = +ve and -nve terminals of controlling source                                                                              

    ictrl voltage : hname N1 N2 Vcontrol Voltage                     
    ictrl current : fname N1 N2 Vcontrol Current                     
      Vcontrol = current flowing into this +ve terminal of a zero value                                                                   
                 voltage source to measure current                   

  Switches                                                           
    vctrl switch  : sname N1 N2 NC1 NC2  MODELNAME                   
    ictrl switch  : wname N1 N2 Vcontrol MODELNAME                   

  Semiconductor Devices                                              
    diode         : dname N+ N-       MODELNAME                      
    bjt           : qname NC NB NE    MODELNAME                      
    mosfet        : mname ND NG NS NB MODELNAME L=length W=width                                                                          

  Models                                                             
    diode         : .model MODELNAME D   [IS=saturation current] [N=emission coefficient]                                                 
                                         [Rs=series resistance] [CJ0=junction capacitance] [Tt=transit time]                              
                                         [BV=reverse breakdown voltage] [IBV=reverse breakdown current]                                   
    mosfet        : .model MODELNAME (N|P)MOS  [KP=uCox] [VT0=threshold] [lambda=] [gamma=] ...                                           
    bjt           : .model MODELNAME (NPN|PNP) [BF=] [IS=] [VAF=]                                                                         
    switch        : .model MODELNAME (SW|CSW)  [RON=on resistance]    [ROFF=off resistance]                                               
                                               [VT=threshold voltage] [VH=hysteresis voltage]                                             
                                               [IT=threshold current] [IT=hysteresis current]                                             

  Hybrid Models (xspice) See Ch 8.3 of ngspice manual                
  Digital Models (xspice) See Ch 8.4 of ngspice manual               
    aname ... model                                                  
    .model name type [properties ...]                                


  Analysis                                                           
    .tran TSTEP TSTOP [TSTART] [TMAX] [UIC]                          
      UIC - flag to use specified IC instead of solving for quiscent operating point first                                                
    .ac TODO                                                         
    .op TODO                                                         
    .dc TODO                                                         

  Commands                                                           
    .ic V(name)=value ...                                            
    .print ANALYSIS [V(name)] [I(name)] ... <up to 8 vars>           
    .plot  ANALYSIS [V(name)] [I(name)] ... <up to 8 vars>           
       V/I suffixes M=magnitude, DB=magnitude in db, P=phase                                                                              
                    R=real part, I=imaginary part                    


  Subcircuit                                                         
    .subckt CKTNAME N1 N2 …                   
    [circuit cards]
    .ends


    xname N1 ... SUBCIRCUITNAME
```
