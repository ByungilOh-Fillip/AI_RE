#include "SkillComponent.h"

#include "Engine/World.h"

USkillComponent::USkillComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void USkillComponent::BeginPlay()
{
	Super::BeginPlay();
}

void USkillComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
}

void USkillComponent::MarkSkillAsUsed(int32 SkillSlot)
{
    float CurrentTime = GetWorld()->GetTimeSeconds();

    if (SkillSlot == 0) LightSkill.LastUseTime = CurrentTime;
    else if (SkillSlot == 1) MediumSkill.LastUseTime = CurrentTime;
    else if (SkillSlot == 2) HeavySkill.LastUseTime = CurrentTime;
}
