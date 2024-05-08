import mlvp
import logging

import os
os.sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from env.bundle import *
from env.bpu_top import *
from env.config import *

os.sys.path.append(DUT_PATH)

from UT_FauFTB import *



def set_imm_mode(uFTB):
    imm_mode = uFTB.io_s0_fire_0.xdata.Imme
    need_to_write_imm = ["io_s0_fire_0", "io_s0_fire_1", "io_s0_fire_2", "io_s0_fire_3",
                        "io_s1_fire_0", "io_s2_fire_0", "io_in_bits_s0_pc_0", "io_in_bits_s0_pc_1",
                        "io_in_bits_s0_pc_2", "io_in_bits_s0_pc_3"]
    for name in need_to_write_imm:
        getattr(uFTB, name).xdata.SetWriteMode(imm_mode)


async def uftb_test(uFTB):
    uFTB_update = UpdateBundle.from_prefix(uFTB, "io_update_")
    uFTB_out = BranchPredictionResp.from_prefix(uFTB, "io_out_")
    pipeline_ctrl = PipelineCtrlBundle.from_prefix(uFTB, "io_")
    enable_ctrl = EnableCtrlBundle.from_prefix(uFTB, "io_ctrl_")

    mlvp.create_task(mlvp.start_clock(uFTB))
    mlvp.create_task(BPUTop(uFTB, uFTB_out, uFTB_update, pipeline_ctrl, enable_ctrl).run())

    await ClockCycles(uFTB, MAX_CYCLE)



import mlvp.funcov as fc
from mlvp.reporter import *

def test_uftb(request):
    # Create DUT
    uFTB = DUTFauFTB(waveform_filename="uftb_with_ftq.fst", coverage_filename="uftb_with_ftq_coverage.dat")
    uFTB.init_clock("clock")
    set_imm_mode(uFTB)

    # Set Coverage
    g1 = fc.CovGroup("interaction")
    g1.add_watch_point(uFTB.reset, { "reset": fc.Eq(1), }, name="reset")
    g1.add_watch_point(uFTB.io_ctrl_ubtb_enable, { "ubtb_enable": fc.Eq(1), }, name="ubtb_enable")
    g1.add_watch_point(uFTB.io_s0_fire_0, { "s0_fire": fc.Eq(1), }, name="s0_fire_0")
    g1.add_watch_point(uFTB.io_s1_fire_0, { "s1_fire": fc.Eq(1), }, name="s1_fire_0")
    g1.add_watch_point(uFTB.io_s2_fire_0, { "s2_fire": fc.Eq(1), }, name="s2_fire_0")
    g1.add_watch_point(uFTB.io_update_valid, { "update_valid": fc.Eq(1), }, name="update_valid")

    g2 = fc.CovGroup("ftb_entry")
    g2.add_watch_point(uFTB.io_out_s1_full_pred_0_hit, { "hit": fc.Eq(1), "not_hit": fc.Eq(0) }, name="s1_full_pred_0_hit")
    g2.add_watch_point(uFTB.io_out_s1_full_pred_3_fallThroughErr, { "fallThroughErr": fc.Eq(1), "not_fallThroughErr": fc.Eq(0) }, name="s1_full_pred_3_fallThroughErr")
    g2.add_watch_point(uFTB.io_out_s1_full_pred_0_slot_valids_0, { "slot_valids_0": fc.Eq(1), "slot_valids_0_invalid": fc.Eq(0) }, name="s1_full_pred_0_slot_valids_0")
    g2.add_watch_point(uFTB.io_out_s1_full_pred_0_slot_valids_1, { "slot_valids_1": fc.Eq(1), "slot_valids_1_invalid": fc.Eq(0) }, name="s1_full_pred_0_slot_valids_1")
    g2.add_watch_point(uFTB.io_out_s1_full_pred_0_br_taken_mask_0, { "br_taken_mask_0": fc.Eq(1), "br_taken_mask_0_invalid": fc.Eq(0) }, name="s1_full_pred_0_br_taken_mask_0")
    g2.add_watch_point(uFTB.io_out_s1_full_pred_0_br_taken_mask_1, { "br_taken_mask_1": fc.Eq(1), "br_taken_mask_1_invalid": fc.Eq(0) }, name="s1_full_pred_0_br_taken_mask_1")
    g2.add_watch_point(uFTB.io_out_s1_full_pred_0_is_br_sharing, { "is_br_sharing": fc.Eq(1), "is_br_sharing_invalid": fc.Eq(0) }, name="s1_full_pred_0_is_br_sharing")

    uFTB.xclock.StepRis(lambda _: g1.sample())
    uFTB.xclock.StepRis(lambda _: g2.sample())

    # Run the test
    mlvp.setup_logging(log_level=logging.INFO, log_file="uftb_with_ftq.log")
    mlvp.run(uftb_test(uFTB))
    uFTB.finalize()

    pred_stat.summary()
    set_func_coverage(request, [g1, g2])
    set_line_coverage(request, "uftb_with_ftq_coverage.dat")
