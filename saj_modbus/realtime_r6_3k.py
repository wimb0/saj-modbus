"""R6 3-15K realtime map (0x4000-0x40FD, 2022 map PDF 4.2.2).

Split into contiguous components so no single read exceeds the Modbus
125-register limit. Field order follows the PDF; signedness follows the
Int16/UInt16 column; scales follow the multiplier column.
"""

from __future__ import annotations

from modbus_connection.model import Component, integer, uint32

from .fields import DateTimeField
from .measure import mgauge, minteger, muint32


class R6_3KHeader(Component):
    """Clock, mode, faults, temps, ISO, DRM (0x4000-0x4021)."""

    datetime = DateTimeField(0x4000, count=4)
    mpvmode = integer(0x4004, signed=False)
    hfaultmsg = uint32(0x4005)
    mfaultmsg = uint32(0x4007)
    mfaultmsg2 = uint32(0x4009)
    bmsfaultmsg = uint32(0x400B)
    errorcount = minteger(0x400F, signed=False)
    sinktempc = mgauge(0x4010, 0.1)
    ambtempc = mgauge(0x4011, 0.1)
    gfci = minteger(0x4012)
    iso1 = minteger(0x4013, signed=False)
    iso2 = minteger(0x4014, signed=False)
    iso3 = minteger(0x4015, signed=False)
    iso4 = minteger(0x4016, signed=False)
    drm_hw = minteger(0x4017, signed=False)
    drm_sw = minteger(0x4018, signed=False)
    conntime = minteger(0x4019, signed=False)
    errordatasn = minteger(0x401A, signed=False)
    settingdatasn = minteger(0x401B, signed=False)
    fcastrigger = minteger(0x401C, signed=False)


class R6_3KBattery(Component):
    """App mode + battery setpoints/state (0x4022-0x4030)."""

    setappmode = integer(0x4022)
    invdischgpowerset = minteger(0x4023)
    invchgpowerset = minteger(0x4024)
    batdiscurrset = mgauge(0x4025, 0.1)
    batchgcurrset = mgauge(0x4026, 0.1)
    batstatus = integer(0x4027, signed=False)
    batprotocol = integer(0x4028)
    batchgsocuplimit = minteger(0x4029)
    batdissoclowlimit = minteger(0x402A)
    batdodset = minteger(0x402B)
    batressoc = minteger(0x402C)
    bmschgvoltset = mgauge(0x402D, 0.1)
    bmsdispowerset = minteger(0x402E)
    bmschgpowerset = minteger(0x402F)
    metermodeset = integer(0x4030)


class R6_3KGrid(Component):
    """R/S/T grid meters (0x4031-0x4045)."""

    rgridvolt = mgauge(0x4031, 0.1, signed=False)
    rgridcurr = mgauge(0x4032, 0.01)
    rgridfreq = mgauge(0x4033, 0.01, signed=False)
    rgriddci = minteger(0x4034)
    rgridpowerwatt = minteger(0x4035)
    rgridpowerva = minteger(0x4036, signed=False)
    rgridpowerpf = mgauge(0x4037, 0.001)
    sgridvolt = mgauge(0x4038, 0.1, signed=False)
    sgridcurr = mgauge(0x4039, 0.01)
    sgridfreq = mgauge(0x403A, 0.01, signed=False)
    sgriddci = minteger(0x403B)
    sgridpowerwatt = minteger(0x403C)
    sgridpowerva = minteger(0x403D, signed=False)
    sgridpowerpf = mgauge(0x403E, 0.001)
    tgridvolt = mgauge(0x403F, 0.1, signed=False)
    tgridcurr = mgauge(0x4040, 0.01)
    tgridfreq = mgauge(0x4041, 0.01, signed=False)
    tgriddci = minteger(0x4042)
    tgridpowerwatt = minteger(0x4043)
    tgridpowerva = minteger(0x4044, signed=False)
    tgridpowerpf = mgauge(0x4045, 0.001)


class R6_3KInv(Component):
    """R/S/T inverting side (0x4046-0x4054)."""

    rinvvolt = mgauge(0x4046, 0.1, signed=False)
    rinvcurr = mgauge(0x4047, 0.01)
    rinvfreq = mgauge(0x4048, 0.01, signed=False)
    rinvpowerwatt = minteger(0x4049)
    rinvpowerva = minteger(0x404A, signed=False)
    sinvvolt = mgauge(0x404B, 0.1, signed=False)
    sinvcurr = mgauge(0x404C, 0.01)
    sinvfreq = mgauge(0x404D, 0.01, signed=False)
    sinvpowerwatt = minteger(0x404E)
    sinvpowerva = minteger(0x404F, signed=False)
    tinvvolt = mgauge(0x4050, 0.1, signed=False)
    tinvcurr = mgauge(0x4051, 0.01)
    tinvfreq = mgauge(0x4052, 0.01, signed=False)
    tinvpowerwatt = minteger(0x4053)
    tinvpowerva = minteger(0x4054, signed=False)


class R6_3KOutput(Component):
    """R/S/T output side (0x4055-0x4066)."""

    routvolt = mgauge(0x4055, 0.1, signed=False)
    routcurr = mgauge(0x4056, 0.01, signed=False)
    routfreq = mgauge(0x4057, 0.01, signed=False)
    routdvi = minteger(0x4058)
    routpowerwatt = minteger(0x4059, signed=False)
    routpowerva = minteger(0x405A, signed=False)
    soutvolt = mgauge(0x405B, 0.1, signed=False)
    soutcurr = mgauge(0x405C, 0.01, signed=False)
    soutfreq = mgauge(0x405D, 0.01, signed=False)
    soutdvi = minteger(0x405E)
    soutpowerwatt = minteger(0x405F, signed=False)
    soutpowerva = minteger(0x4060, signed=False)
    toutvolt = mgauge(0x4061, 0.1, signed=False)
    toutcurr = mgauge(0x4062, 0.01, signed=False)
    toutfreq = mgauge(0x4063, 0.01, signed=False)
    toutdvi = minteger(0x4064)
    toutpowerwatt = minteger(0x4065, signed=False)
    toutpowerva = minteger(0x4066, signed=False)


class R6_3KBusBatPv(Component):
    """Bus, battery and PV1-4 (0x4067-0x407C)."""

    busvoltm = mgauge(0x4067, 0.1, signed=False)
    busvolts = mgauge(0x4068, 0.1, signed=False)
    batvolt = mgauge(0x4069, 0.1, signed=False)
    batcurr = mgauge(0x406A, 0.01)
    batcurr1 = mgauge(0x406B, 0.01)
    batcurr2 = mgauge(0x406C, 0.01)
    batpower = minteger(0x406D)
    battempc = mgauge(0x406E, 0.1)
    batenergypercent = mgauge(0x406F, 0.01, signed=False)
    pv1volt = mgauge(0x4071, 0.1, signed=False)
    pv1curr = mgauge(0x4072, 0.01, signed=False)
    pv1power = minteger(0x4073, signed=False)
    pv2volt = mgauge(0x4074, 0.1, signed=False)
    pv2curr = mgauge(0x4075, 0.01, signed=False)
    pv2power = minteger(0x4076, signed=False)
    pv3volt = mgauge(0x4077, 0.1, signed=False)
    pv3curr = mgauge(0x4078, 0.01, signed=False)
    pv3power = minteger(0x4079, signed=False)
    pv4volt = mgauge(0x407A, 0.1, signed=False)
    pv4curr = mgauge(0x407B, 0.01, signed=False)
    pv4power = minteger(0x407C, signed=False)


class R6_3KStrings(Component):
    """PV string currents (0x407D-0x408C)."""

    pv1strcurr1 = mgauge(0x407D, 0.01, signed=False)
    pv1strcurr2 = mgauge(0x407E, 0.01, signed=False)
    pv1strcurr3 = mgauge(0x407F, 0.01, signed=False)
    pv1strcurr4 = mgauge(0x4080, 0.01, signed=False)
    pv2strcurr1 = mgauge(0x4081, 0.01, signed=False)
    pv2strcurr2 = mgauge(0x4082, 0.01, signed=False)
    pv2strcurr3 = mgauge(0x4083, 0.01, signed=False)
    pv2strcurr4 = mgauge(0x4084, 0.01, signed=False)
    pv3strcurr1 = mgauge(0x4085, 0.01, signed=False)
    pv3strcurr2 = mgauge(0x4086, 0.01, signed=False)
    pv3strcurr3 = mgauge(0x4087, 0.01, signed=False)
    pv3strcurr4 = mgauge(0x4088, 0.01, signed=False)
    pv4strcurr1 = mgauge(0x4089, 0.01, signed=False)
    pv4strcurr2 = mgauge(0x408A, 0.01, signed=False)
    pv4strcurr3 = mgauge(0x408B, 0.01, signed=False)
    pv4strcurr4 = mgauge(0x408C, 0.01, signed=False)


class R6_3KFlows(Component):
    """On-grid side, flow directions and power totals (0x408D-0x40B2)."""

    rongridoutvolt = mgauge(0x408D, 0.1, signed=False)
    rongridoutcurr = mgauge(0x408E, 0.01, signed=False)
    rongridoutfreq = mgauge(0x408F, 0.01, signed=False)
    rongridoutpowerwatt = minteger(0x4090, signed=False)
    songridoutvolt = mgauge(0x4091, 0.1, signed=False)
    songridoutpowerwatt = minteger(0x4092, signed=False)
    tongridoutvolt = mgauge(0x4093, 0.1, signed=False)
    tongridoutpowerwatt = minteger(0x4094, signed=False)
    pv_direction = integer(0x4095, signed=False)
    battery_direction = integer(0x4096)
    grid_direction = integer(0x4097)
    output_direction = integer(0x4098, signed=False)
    pvconsumpwatt = minteger(0x4099)
    gridconsumpwatt = minteger(0x409A)
    gridfeedinpvwatt = minteger(0x409B)
    gridfeedinbatwatt = minteger(0x409C)
    batconsumpwatt = minteger(0x409D)
    batchg_pvwatt = minteger(0x409E)
    batchg_gridwatt = minteger(0x409F)
    systotalloadwatt = minteger(0x40A0)
    ct_gridpowerwatt = minteger(0x40A1)
    ct_gridpowerva = minteger(0x40A2)
    ct_pvpowerwatt = minteger(0x40A3)
    ct_pvpowerva = minteger(0x40A4)
    totalpvpower = minteger(0x40A5)
    totalbatterypower = minteger(0x40A6)
    totalgridpowerwatt = minteger(0x40A7)
    totalgridpowerva = minteger(0x40A8)
    totalinvpowerwatt = minteger(0x40A9)
    totalinvpowerva = minteger(0x40AA)
    backuptoloadpowerwatt = minteger(0x40AB, signed=False)
    backuptoloadpowerva = minteger(0x40AC, signed=False)
    sysgridpower = minteger(0x40AD)
    input_avg_power_5min_max = minteger(0x40AE, signed=False)
    output_avg_power_5min_max = minteger(0x40AF, signed=False)
    rintelligentloadpower = minteger(0x40B0, signed=False)
    sintelligentloadpower = minteger(0x40B1, signed=False)
    tintelligentloadpower = minteger(0x40B2, signed=False)


class R6_3KEnergy(Component):
    """Hours + energy ledger (0x40BC-0x40FD)."""

    today_hour = mgauge(0x40BC, 0.1, signed=False)
    total_hour = muint32(0x40BD, scale=0.1)
    today_pvenergy = muint32(0x40BF, scale=0.01)
    month_pvenergy = muint32(0x40C1, scale=0.01)
    year_pvenergy = muint32(0x40C3, scale=0.01)
    total_pvenergy = muint32(0x40C5, scale=0.01)
    today_batchgenergy = muint32(0x40C7, scale=0.01)
    month_batchgenergy = muint32(0x40C9, scale=0.01)
    year_batchgenergy = muint32(0x40CB, scale=0.01)
    total_batchgenergy = muint32(0x40CD, scale=0.01)
    today_batdisenergy = muint32(0x40CF, scale=0.01)
    month_batdisenergy = muint32(0x40D1, scale=0.01)
    year_batdisenergy = muint32(0x40D3, scale=0.01)
    total_batdisenergy = muint32(0x40D5, scale=0.01)
    today_invgenenergy = muint32(0x40D7, scale=0.01)
    month_invgenenergy = muint32(0x40D9, scale=0.01)
    year_invgenenergy = muint32(0x40DB, scale=0.01)
    total_invgenenergy = muint32(0x40DD, scale=0.01)
    today_totalloadenergy = muint32(0x40DF, scale=0.01)
    month_totalloadenergy = muint32(0x40E1, scale=0.01)
    year_totalloadenergy = muint32(0x40E3, scale=0.01)
    total_totalloadenergy = muint32(0x40E5, scale=0.01)
    today_backuploadenergy = muint32(0x40E7, scale=0.01)
    month_backuploadenergy = muint32(0x40E9, scale=0.01)
    year_backuploadenergy = muint32(0x40EB, scale=0.01)
    total_backuploadenergy = muint32(0x40ED, scale=0.01)
    today_sellenergy = muint32(0x40EF, scale=0.01)
    month_sellenergy = muint32(0x40F1, scale=0.01)
    year_sellenergy = muint32(0x40F3, scale=0.01)
    total_sellenergy = muint32(0x40F5, scale=0.01)
    today_feedinenergy = muint32(0x40F7, scale=0.01)
    month_feedinenergy = muint32(0x40F9, scale=0.01)
    year_feedinenergy = muint32(0x40FB, scale=0.01)
    total_feedinenergy = muint32(0x40FD, scale=0.01)
