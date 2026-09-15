# Fisherman's Horizon GBA - Butano project
# Framework compatibility target: Butano 21.7.1

TARGET := Fishermans_Horizon_GBA
BUILD := build
LIBBUTANO ?= ../butano/butano
PYTHON ?= python3

SOURCES := src
INCLUDES := include
DATA :=
GRAPHICS := graphics
AUDIO := audio
AUDIOBACKEND := maxmod
AUDIOTOOL :=
DMGAUDIO :=
DMGAUDIOBACKEND := default

ROMTITLE := FISH HORIZON
ROMCODE := FHGA

USERFLAGS :=
USERCXXFLAGS :=
USERASFLAGS :=
USERLDFLAGS :=
USERLIBDIRS :=
USERLIBS :=
DEFAULTLIBS :=
STACKTRACE :=
USERBUILD :=
EXTTOOL :=

ifndef LIBBUTANOABS
export LIBBUTANOABS := $(realpath $(LIBBUTANO))
endif

include $(LIBBUTANOABS)/butano.mak
