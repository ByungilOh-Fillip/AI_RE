#include "AIRECompanionGameplayTags.h"

namespace AIRECompanionGameplayTags
{
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(StateDisabled, "State.Companion.Disabled", "Companion cannot select normal behavior.");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(StateDisabledDead, "State.Companion.Disabled.Dead", "Companion health is depleted.");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(DataDamage, "Data.Companion.Damage", "Negative health delta supplied by a damage Gameplay Effect spec.");
}
