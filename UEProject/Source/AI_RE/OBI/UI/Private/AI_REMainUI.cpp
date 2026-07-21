// Fill out your copyright notice in the Description page of Project Settings.


#include "AI_REMainUI.h"

#include "AI_REStatePointBar.h"
#include "AI_REStatusComponent.h"


void UAI_REMainUI::InitializeHUD(TObjectPtr<UAI_REStatusComponent> InStatus)
{
	if (InStatus == nullptr) return; 
	
	InStatus -> OnHPChanged.AddDynamic(this, &UAI_REMainUI::UpdateHPBar);
	InStatus -> OnSPChanged.AddDynamic(this, &UAI_REMainUI::UpdateSPBar);
	InStatus -> OnHungerChanged.AddDynamic(this, &UAI_REMainUI::UpdateHungerBar);
	
	UpdateHPBar(InStatus -> CurrentHP, InStatus -> MaxHP);
	UpdateSPBar(InStatus -> CurrentSP, InStatus -> MaxSP);
	UpdateHungerBar(InStatus -> CurrentHunger, InStatus -> MaxHunger);
}

void UAI_REMainUI::UpdateHPBar(float Current, float Max)
{
	if (HPBar && Max > 0.f)
	{
		HPBar->SetTargetPercent(Current/Max);
	}
}

void UAI_REMainUI::UpdateSPBar(float Current, float Max)
{
	if (SPBar && Max > 0.f)
	{
		SPBar->SetTargetPercent(Current/Max);
	}
}

void UAI_REMainUI::UpdateHungerBar(float Current, float Max)
{
	if (HungerBar && Max > 0.f)
	{
		HungerBar->SetTargetPercent(Current/Max);
	}
}
