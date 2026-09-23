"""R6 3-15K realtime map (0x4000-0x40FD, 2022 map PDF 4.2.2).

Split into contiguous components so no single read exceeds the Modbus
125-register limit. Field order follows the PDF; signedness follows the
Int16/UInt16 column; scales follow the multiplier column.
"""

from __future__ import annotations

from modbus_connection.model import Component, gauge, integer, uint32

from .fields import DateTimeField


class R6_3KHeader(Component):
    """Clock, mode, faults, temps, ISO, DRM (0x4000-0x4021)."""

    datetime = DateTimeField(0x4000, count=4)
    mpvmode = integer(0x4004, signed=False)
    hfaultmsg = uint32(0x4005)
    mfaultmsg = uint32(0x4007)
    mfaultmsg2 = uint32(0x4009)
    bmsfaultmsg = uint32(0x400B)
    errorcount = integer(0x400F, signed=False)
    sinktempc = gauge(0x4010, 0.1)
    ambtempc = gauge(0x4011, 0.1)
    gfci = integer(0x4012)
    iso1 = integer(0x4013, signed=False)
    iso2 = integer(0x4014, signed=False)
    iso3 = integer(0x4015, signed=False)
    iso4 = integer(0x4016, signed=False)
    drm_hw = integer(0x4017, signed=False)
    drm_sw = integer(0x4018, signed=False)
    conntime = integer(0x4019, signed=False)
    errordatasn = integer(0x401A, signed=False)
    settingdatasn = integer(0x401B, signed=False)
    fcastrigger = integer(0x401C, signed=False)


class R6_3KBattery(Component):
    """App mode + battery setpoints/state (0x4022-0x4030)."""

    setappmode = integer(0x4022)
    invdischgpowerset = integer(0x4023)
    invchgpowerset = integer(0x4024)
    batdiscurrset = gauge(0x4025, 0.1)
    batchgcurrset = gauge(0x4026, 0.1)
    batstatus = integer(0x4027, signed=False)
    batprotocol = integer(0x4028)
    batchgsocuplimit = integer(0x4029)
    batdissoclowlimit = integer(0x402A)
    batdodset = integer(0x402B)
    batressoc = integer(0x402C)
    bmschgvoltset = gauge(0x402D, 0.1)
    bmsdispowerset = integer(0x402E)
    bmschgpowerset = integer(0x402F)
    metermodeset = integer(0x4030)


class R6_3KGrid(Component):
    """R/S/T grid meters (0x4031-0x4045)."""

    rgridvolt = gauge(0x4031, 0.1, signed=False)
    rgridcurr = gauge(0x4032, 0.01)
    rgridfreq = gauge(0x4033, 0.01, signed=False)
    rgriddci = integer(0x4034)
    rgridpowerwatt = integer(0x4035)
    rgridpowerva = integer(0x4036, signed=False)
    rgridpowerpf = gauge(0x4037, 0.001)
    sgridvolt = gauge(0x4038, 0.1, signed=False)
    sgridcurr = gauge(0x4039, 0.01)
    sgridfreq = gauge(0x403A, 0.01, signed=False)
    sgriddci = integer(0x403B)
    sgridpowerwatt = integer(0x403C)
    sgridpowerva = integer(0x403D, signed=False)
    sgridpowerpf = gauge(0x403E, 0.001)
    tgridvolt = gauge(0x403F, 0.1, signed=False)
    tgridcurr = gauge(0x4040, 0.01)
    tgridfreq = gauge(0x4041, 0.01, signed=False)
    tgriddci = integer(0x4042)
    tgridpowerwatt = integer(0x4043)
    tgridpowerva = integer(0x4044, signed=False)
    tgridpowerpf = gauge(0x4045, 0.001)


class R6_3KInv(Component):
    """R/S/T inverting side (0x4046-0x4054)."""

    rinvvolt = gauge(0x4046, 0.1, signed=False)
    rinvcurr = gauge(0x4047, 0.01)
    rinvfreq = gauge(0x4048, 0.01, signed=False)
    rinvpowerwatt = integer(0x4049)
    rinvpowerva = integer(0x404A, signed=False)
    sinvvolt = gauge(0x404B, 0.1, signed=False)
    sinvcurr = gauge(0x404C, 0.01)
    sinvfreq = gauge(0x404D, 0.01, signed=False)
    sinvpowerwatt = integer(0x404E)
    sinvpowerva = integer(0x404F, signed=False)
    tinvvolt = gauge(0x4050, 0.1, signed=False)
    tinvcurr = gauge(0x4051, 0.01)
    tinvfreq = gauge(0x4052, 0.01, signed=False)
    tinvpowerwatt = integer(0x4053)
    tinvpowerva = integer(0x4054, signed=False)


class R6_3KOutput(Component):
    """R/S/T output side (0x4055-0x4066)."""

    routvolt = gauge(0x4055, 0.1, signed=False)
    routcurr = gauge(0x4056, 0.01, signed=False)
    routfreq = gauge(0x4057, 0.01, signed=False)
    routdvi = integer(0x4058)
    routpowerwatt = integer(0x4059, signed=False)
    routpowerva = integer(0x405A, signed=False)
    soutvolt = gauge(0x405B, 0.1, signed=False)
    soutcurr = gauge(0x405C, 0.01, signed=False)
    soutfreq = gauge(0x405D, 0.01, signed=False)
    soutdvi = integer(0x405E)
    soutpowerwatt = integer(0x405F, signed=False)
    soutpowerva = integer(0x4060, signed=False)
    toutvolt = gauge(0x4061, 0.1, signed=False)
    toutcurr = gauge(0x4062, 0.01, signed=False)
    toutfreq = gauge(0x4063, 0.01, signed=False)
    toutdvi = integer(0x4064)
    toutpowerwatt = integer(0x4065, signed=False)
    toutpowerva = integer(0x4066, signed=False)


class R6_3KBusBatPv(Component):
    """Bus, battery and PV1-4 (0x4067-0x407C)."""

    busvoltm = gauge(0x4067, 0.1, signed=False)
    busvolts = gauge(0x4068, 0.1, signed=False)
    batvolt = gauge(0x4069, 0.1, signed=False)
    batcurr = gauge(0x406A, 0.01)
    batcurr1 = gauge(0x406B, 0.01)
    batcurr2 = gauge(0x406C, 0.01)
    batpower = integer(0x406D)
    battempc = gauge(0x406E, 0.1)
    batenergypercent = gauge(0x406F, 0.01, signed=False)
    pv1volt = gauge(0x4071, 0.1, signed=False)
    pv1curr = gauge(0x4072, 0.01, signed=False)
    pv1power = integer(0x4073, signed=False)
    pv2volt = gauge(0x4074, 0.1, signed=False)
    pv2curr = gauge(0x4075, 0.01, signed=False)
    pv2power = integer(0x4076, signed=False)
    pv3volt = gauge(0x4077, 0.1, signed=False)
    pv3curr = gauge(0x4078, 0.01, signed=False)
    pv3power = integer(0x4079, signed=False)
    pv4volt = gauge(0x407A, 0.1, signed=False)
    pv4curr = gauge(0x407B, 0.01, signed=False)
    pv4power = integer(0x407C, signed=False)


class R6_3KStrings(Component):
    """PV string currents (0x407D-0x408C)."""

    pv1strcurr1 = gauge(0x407D, 0.01, signed=False)
    pv1strcurr2 = gauge(0x407E, 0.01, signed=False)
    pv1strcurr3 = gauge(0x407F, 0.01, signed=False)
    pv1strcurr4 = gauge(0x4080, 0.01, signed=False)
    pv2strcurr1 = gauge(0x4081, 0.01, signed=False)
    pv2strcurr2 = gauge(0x4082, 0.01, signed=False)
    pv2strcurr3 = gauge(0x4083, 0.01, signed=False)
    pv2strcurr4 = gauge(0x4084, 0.01, signed=False)
    pv3strcurr1 = gauge(0x4085, 0.01, signed=False)
    pv3strcurr2 = gauge(0x4086, 0.01, signed=False)
    pv3strcurr3 = gauge(0x4087, 0.01, signed=False)
    pv3strcurr4 = gauge(0x4088, 0.01, signed=False)
    pv4strcurr1 = gauge(0x4089, 0.01, signed=False)
    pv4strcurr2 = gauge(0x408A, 0.01, signed=False)
    pv4strcurr3 = gauge(0x408B, 0.01, signed=False)
    pv4strcurr4 = gauge(0x408C, 0.01, signed=False)


class R6_3KFlows(Component):
    """On-grid side, flow directions and power totals (0x408D-0x40B2)."""

    rongridoutvolt = gauge(0x408D, 0.1, signed=False)
    rongridoutcurr = gauge(0x408E, 0.01, signed=False)
    rongridoutfreq = gauge(0x408F, 0.01, signed=False)
    rongridoutpowerwatt = integer(0x4090, signed=False)
    songridoutvolt = gauge(0x4091, 0.1, signed=False)
    songridoutpowerwatt = integer(0x4092, signed=False)
    tongridoutvolt = gauge(0x4093, 0.1, signed=False)
    tongridoutpowerwatt = integer(0x4094, signed=False)
    pv_direction = integer(0x4095, signed=False)
    battery_direction = integer(0x4096)
    grid_direction = integer(0x4097)
    output_direction = integer(0x4098, signed=False)
    pvconsumpwatt = integer(0x4099)
    gridconsumpwatt = integer(0x409A)
    gridfeedinpvwatt = integer(0x409B)
    gridfeedinbatwatt = integer(0x409C)
    batconsumpwatt = integer(0x409D)
    batchg_pvwatt = integer(0x409E)
    batchg_gridwatt = integer(0x409F)
    systotalloadwatt = integer(0x40A0)
    ct_gridpowerwatt = integer(0x40A1)
    ct_gridpowerva = integer(0x40A2)
    ct_pvpowerwatt = integer(0x40A3)
    ct_pvpowerva = integer(0x40A4)
    totalpvpower = integer(0x40A5)
    totalbatterypower = integer(0x40A6)
    totalgridpowerwatt = integer(0x40A7)
    totalgridpowerva = integer(0x40A8)
    totalinvpowerwatt = integer(0x40A9)
    totalinvpowerva = integer(0x40AA)
    backuptoloadpowerwatt = integer(0x40AB, signed=False)
    backuptoloadpowerva = integer(0x40AC, signed=False)
    sysgridpower = integer(0x40AD)
    input_avg_power_5min_max = integer(0x40AE, signed=False)
    output_avg_power_5min_max = integer(0x40AF, signed=False)
    rintelligentloadpower = integer(0x40B0, signed=False)
    sintelligentloadpower = integer(0x40B1, signed=False)
    tintelligentloadpower = integer(0x40B2, signed=False)


class R6_3KEnergy(Component):
    """Hours + energy ledger (0x40BC-0x40FD)."""

    today_hour = gauge(0x40BC, 0.1, signed=False)
    total_hour = uint32(0x40BD, scale=0.1)
    today_pvenergy = uint32(0x40BF, scale=0.01)
    month_pvenergy = uint32(0x40C1, scale=0.01)
    year_pvenergy = uint32(0x40C3, scale=0.01)
    total_pvenergy = uint32(0x40C5, scale=0.01)
    today_batchgenergy = uint32(0x40C7, scale=0.01)
    month_batchgenergy = uint32(0x40C9, scale=0.01)
    year_batchgenergy = uint32(0x40CB, scale=0.01)
    total_batchgenergy = uint32(0x40CD, scale=0.01)
    today_batdisenergy = uint32(0x40CF, scale=0.01)
    month_batdisenergy = uint32(0x40D1, scale=0.01)
    year_batdisenergy = uint32(0x40D3, scale=0.01)
    total_batdisenergy = uint32(0x40D5, scale=0.01)
    today_invgenenergy = uint32(0x40D7, scale=0.01)
    month_invgenenergy = uint32(0x40D9, scale=0.01)
    year_invgenenergy = uint32(0x40DB, scale=0.01)
    total_invgenenergy = uint32(0x40DD, scale=0.01)
    today_totalloadenergy = uint32(0x40DF, scale=0.01)
    month_totalloadenergy = uint32(0x40E1, scale=0.01)
    year_totalloadenergy = uint32(0x40E3, scale=0.01)
    total_totalloadenergy = uint32(0x40E5, scale=0.01)
    today_backuploadenergy = uint32(0x40E7, scale=0.01)
    month_backuploadenergy = uint32(0x40E9, scale=0.01)
    year_backuploadenergy = uint32(0x40EB, scale=0.01)
    total_backuploadenergy = uint32(0x40ED, scale=0.01)
    today_sellenergy = uint32(0x40EF, scale=0.01)
    month_sellenergy = uint32(0x40F1, scale=0.01)
    year_sellenergy = uint32(0x40F3, scale=0.01)
    total_sellenergy = uint32(0x40F5, scale=0.01)
    today_feedinenergy = uint32(0x40F7, scale=0.01)
    month_feedinenergy = uint32(0x40F9, scale=0.01)
    year_feedinenergy = uint32(0x40FB, scale=0.01)
    total_feedinenergy = uint32(0x40FD, scale=0.01)
