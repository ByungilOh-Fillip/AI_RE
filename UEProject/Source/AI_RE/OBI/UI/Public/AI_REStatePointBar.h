// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AI_REStatePointBar.generated.h"

/**
 * 
 */
class UImage;

UCLASS()
class AI_RE_API UAI_REStatePointBar : public UUserWidget
{
	GENERATED_BODY()
	
private:
	float TargetPercent;
	float CurrentPercent;
	
	FTimerHandle SmoothTimerHandle;
	
	void SmoothBar();
	
protected:
	UPROPERTY(meta=(BindWidget))
	TObjectPtr<UImage> StateBar;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar Settings")
	TObjectPtr<class UMaterialInterface> CustomBarMaterial;
	
	virtual void NativePreConstruct() override;
	
public:
	void SetTargetPercent(float NewPercent);
};
