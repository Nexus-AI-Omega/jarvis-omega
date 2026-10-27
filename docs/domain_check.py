#!/usr/bin/env python3
"""Korrigierte, konsolidierte Verfügbarkeitsprüfung — immer mit vollständigem Domainnamen (FQDN)."""
import json, urllib.request, urllib.error, concurrent.futures as cf
UA={"User-Agent":"jarvis-omega-domain-scout/1.0","Accept":"application/rdap+json, application/json"}
RDAP={"com":"https://rdap.verisign.com/com/v1/domain/{}",
      "net":"https://rdap.verisign.com/net/v1/domain/{}",
      "de":"https://rdap.denic.de/domain/{}",
      "io":"https://rdap.identitydigital.services/rdap/domain/{}"}

def rdap(domain, tld):
    try:
        urllib.request.urlopen(urllib.request.Request(RDAP[tld].format(domain), headers=UA), timeout=15)
        return "belegt"
    except urllib.error.HTTPError as e:
        return "FREI" if e.code==404 else f"unklar({e.code})"
    except Exception: return "fehler"

def ns(domain):
    try:
        with urllib.request.urlopen(urllib.request.Request(f"https://dns.google/resolve?name={domain}&type=NS",headers=UA),timeout=15) as r:
            d=json.loads(r.read().decode())
        return "FREI" if d.get("Status")==3 else ("belegt" if d.get("Answer") else "unklar(kein NS)")
    except Exception: return "fehler"

def check(domain):
    tld = domain.rsplit(".",1)[1]
    first = ns(domain) if tld=="gg" else rdap(domain, tld)
    second = ns(domain)          # zweite, unabhängige Quelle
    if first=="FREI" and second=="FREI": return "FREI"
    if first=="belegt" or second=="belegt": return "belegt"
    return f"{first}/{second}"

NAMES = ["jarvisguard","starknexus","omegarealm","aegisrealm","arcforge","vaultcraft","ironspire",
         "everforge","stormforge","brightforge","cobaltcraft","novaforge","redstoneguard","deepvale",
         "ironvale","obsidiangate","lumenmc","astraforge","vireo","zyra","kestrelmc","onyxrealm",
         "embercraft","quarrymc","starkrealm","jarvisrealm","jarismic","starkmc","nexusrealm",
         "ironrealm","redstonerealm","omegacraftnetwork","aurelithmc","cobaltnx","sentinelcraft",
         "starkcraft","jarviscraft","omegacraft","aegismc","aegiscraft","redstonenexus"]
TLDS=["com","de","gg","net"]
jobs=[f"{n}.{t}" for n in NAMES for t in TLDS]
res={}
with cf.ThreadPoolExecutor(max_workers=12) as ex:
    for d,s in zip(jobs, ex.map(check, jobs)): res[d]=s
json.dump(res, open("verified.json","w"), indent=1, ensure_ascii=False)

free=[d for d,s in res.items() if s=="FREI"]
print(f"geprüft: {len(res)} | FREI: {len(free)} | belegt/unklar: {len(res)-len(free)}\n")
print("== NAMEN MIT FREIEM .COM (der Königsweg) ==")
for n in NAMES:
    c=res[f"{n}.com"]
    if c=="FREI":
        print(f"  ✅ {n:18s} .com FREI | .de: {res[n+'.de']:7s} | .gg: {res[n+'.gg']:7s} | .net: {res[n+'.net']}")
print("\n== .GG FREI (Minecraft-Standard-TLD), .com aber belegt ==")
for n in NAMES:
    if res[f"{n}.gg"]=="FREI" and res[f"{n}.com"]=="belegt":
        print(f"  ✅ {n:18s} .gg FREI | .de: {res[n+'.de']:7s} | .com belegt")
